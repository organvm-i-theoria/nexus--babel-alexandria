from __future__ import annotations

import base64
import hashlib
import json
import random
import re
import zlib
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from nexus_babel.models import Branch, BranchCheckpoint, BranchEvent, Document


@dataclass
class DriftResult:
    output_text: str
    diff_summary: dict[str, Any]


class EvolutionService:
    NATURAL_MAP = {
        "th": "þ",
        "ae": "æ",
        "ph": "f",
        "ck": "k",
        "tion": "cion",
    }

    GLYPH_POOL = ["∆", "Æ", "Ω", "§", "☲", "⟁"]
    PHASES = {"expansion", "peak", "compression", "rebirth"}

    def evolve_branch(
        self,
        session: Session,
        parent_branch_id: str | None,
        root_document_id: str | None,
        event_type: str,
        event_payload: dict[str, Any],
        mode: str,
    ) -> tuple[Branch, BranchEvent]:
        payload = self._validate_event_payload(event_type, event_payload)
        parent = None
        lineage_event_count = 0
        if parent_branch_id:
            parent = session.scalar(select(Branch).where(Branch.id == parent_branch_id))
            if not parent:
                raise ValueError(f"Parent branch {parent_branch_id} not found")
            root_document_id = parent.root_document_id
            base_text = str((parent.state_snapshot or {}).get("current_text", ""))
            lineage_event_count = self._lineage_event_count(session, parent)
            expected_parent_event_index = payload.get("expected_parent_event_index")
            if expected_parent_event_index is not None and int(expected_parent_event_index) != lineage_event_count:
                raise ValueError(
                    f"Optimistic concurrency violation: expected_parent_event_index={expected_parent_event_index} actual={lineage_event_count}"
                )
        else:
            if not root_document_id:
                raise ValueError("root_document_id is required when parent_branch_id is not provided")
            doc = session.scalar(select(Document).where(Document.id == root_document_id))
            if not doc:
                raise ValueError(f"Root document {root_document_id} not found")
            base_text = str((doc.provenance or {}).get("extracted_text", ""))

        drift = self._apply_event(base_text, event_type=event_type, event_payload=payload)
        new_hash = hashlib.sha256(drift.output_text.encode("utf-8")).hexdigest()

        new_branch = Branch(
            parent_branch_id=parent.id if parent else None,
            root_document_id=root_document_id,
            name=f"branch-{event_type}",
            mode=mode.upper(),
            state_snapshot={
                "current_text": drift.output_text,
                "phase": payload.get("phase", "expansion"),
                "text_hash": new_hash,
            },
            branch_version=(parent.branch_version + 1) if parent else 1,
        )
        session.add(new_branch)
        session.flush()

        current_event_index = self._next_event_index(session, new_branch.id)
        event_hash = hashlib.sha256(
            f"{new_branch.id}:{current_event_index}:{event_type}:{json.dumps(payload, sort_keys=True)}:{new_hash}".encode("utf-8")
        ).hexdigest()

        event = BranchEvent(
            branch_id=new_branch.id,
            event_index=current_event_index,
            event_type=event_type,
            event_payload=payload,
            payload_schema_version="v2",
            event_hash=event_hash,
            diff_summary=drift.diff_summary,
            result_snapshot={
                "text_hash": new_hash,
                "preview": drift.output_text[:500],
            },
        )
        session.add(event)

        total_lineage_events = lineage_event_count + 1
        if total_lineage_events % 10 == 0:
            session.add(
                BranchCheckpoint(
                    branch_id=new_branch.id,
                    event_index=total_lineage_events,
                    snapshot_hash=new_hash,
                    snapshot_compressed=self._compress_snapshot(new_branch.state_snapshot),
                )
            )

        return new_branch, event

    def get_timeline(self, session: Session, branch_id: str) -> dict[str, Any]:
        branch = session.scalar(select(Branch).where(Branch.id == branch_id))
        if not branch:
            raise ValueError(f"Branch {branch_id} not found")

        lineage = self._lineage(session, branch)
        events: list[BranchEvent] = []
        for node in lineage:
            events.extend(
                session.scalars(
                    select(BranchEvent).where(BranchEvent.branch_id == node.id).order_by(BranchEvent.event_index, BranchEvent.created_at)
                ).all()
            )

        root_text = ""
        if branch.root_document_id:
            doc = session.scalar(select(Document).where(Document.id == branch.root_document_id))
            if doc:
                root_text = str((doc.provenance or {}).get("extracted_text", ""))

        replay_text = root_text
        for event in events:
            replay_text = self._apply_event(replay_text, event.event_type, event.event_payload).output_text

        return {
            "branch": branch,
            "events": events,
            "replay_snapshot": {
                "text_hash": hashlib.sha256(replay_text.encode("utf-8")).hexdigest(),
                "preview": replay_text[:500],
                "event_count": len(events),
            },
        }

    def replay_branch(self, session: Session, branch_id: str) -> dict[str, Any]:
        timeline = self.get_timeline(session, branch_id)
        replay = timeline["replay_snapshot"]
        return {
            "branch_id": branch_id,
            "event_count": replay.get("event_count", 0),
            "text_hash": replay["text_hash"],
            "preview": replay["preview"],
            "replay_snapshot": replay,
        }

    def compare_branches(self, session: Session, left_branch_id: str, right_branch_id: str) -> dict[str, Any]:
        left = self.replay_branch(session, left_branch_id)
        right = self.replay_branch(session, right_branch_id)
        preview_left = left["preview"]
        preview_right = right["preview"]
        distance = self._simple_distance(preview_left, preview_right)
        return {
            "left_branch_id": left_branch_id,
            "right_branch_id": right_branch_id,
            "left_hash": left["text_hash"],
            "right_hash": right["text_hash"],
            "distance": distance,
            "same": left["text_hash"] == right["text_hash"],
            "preview_left": preview_left,
            "preview_right": preview_right,
        }

    def _lineage(self, session: Session, branch: Branch) -> list[Branch]:
        lineage = [branch]
        current = branch
        while current.parent_branch_id:
            parent = session.scalar(select(Branch).where(Branch.id == current.parent_branch_id))
            if not parent:
                break
            lineage.append(parent)
            current = parent
        lineage.reverse()
        return lineage

    def _lineage_event_count(self, session: Session, branch: Branch) -> int:
        lineage = self._lineage(session, branch)
        count = 0
        for node in lineage:
            count += int(
                session.scalar(
                    select(func.count(BranchEvent.id)).where(BranchEvent.branch_id == node.id)
                )
                or 0
            )
        return count

    def _next_event_index(self, session: Session, branch_id: str) -> int:
        max_index = session.scalar(select(func.max(BranchEvent.event_index)).where(BranchEvent.branch_id == branch_id))
        return int(max_index or 0) + 1

    def _validate_event_payload(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = dict(payload or {})
        if "seed" in data:
            data["seed"] = int(data["seed"])

        if event_type == "natural_drift":
            data.setdefault("seed", 0)
            return data

        if event_type == "synthetic_mutation":
            mutation_rate = float(data.get("mutation_rate", 0.08))
            if mutation_rate < 0.0 or mutation_rate > 1.0:
                raise ValueError("mutation_rate must be between 0.0 and 1.0")
            data["mutation_rate"] = mutation_rate
            data.setdefault("seed", 0)
            return data

        if event_type == "phase_shift":
            phase = str(data.get("phase", "expansion")).lower()
            if phase not in self.PHASES:
                raise ValueError(f"phase must be one of {sorted(self.PHASES)}")
            data["phase"] = phase
            data.setdefault("seed", 0)
            return data

        if event_type == "glyph_fusion":
            left = str(data.get("left", "A"))
            right = str(data.get("right", "E"))
            fused = str(data.get("fused", "Æ"))
            if not left or not right or not fused:
                raise ValueError("glyph_fusion requires non-empty left/right/fused")
            data["left"] = left
            data["right"] = right
            data["fused"] = fused
            data.setdefault("seed", 0)
            return data

        raise ValueError(f"Unsupported event_type: {event_type}")

    def _apply_event(self, text: str, event_type: str, event_payload: dict[str, Any]) -> DriftResult:
        seed_input = f"{event_type}:{event_payload.get('seed', '')}:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"
        rng = random.Random(int(hashlib.sha256(seed_input.encode("utf-8")).hexdigest(), 16) % (2**32))
        before_chars = len(text)

        if event_type == "natural_drift":
            out = text
            replacements = 0
            for old, new in self.NATURAL_MAP.items():
                count = out.lower().count(old)
                replacements += count
                out = re.sub(old, new, out, flags=re.IGNORECASE)
            return DriftResult(out, {"event": event_type, "replacements": replacements, "before_chars": before_chars, "after_chars": len(out)})

        if event_type == "synthetic_mutation":
            words = re.findall(r"\w+|\W+", text)
            mutations = 0
            for idx, token in enumerate(words):
                if token.isalpha() and rng.random() < float(event_payload.get("mutation_rate", 0.08)):
                    words[idx] = rng.choice(self.GLYPH_POOL)
                    mutations += 1
            out = "".join(words)
            return DriftResult(out, {"event": event_type, "mutations": mutations, "before_chars": before_chars, "after_chars": len(out)})

        if event_type == "phase_shift":
            phase = str(event_payload.get("phase", "expansion")).lower()
            if phase == "compression":
                out = re.sub(r"([aeiouAEIOU])", "", text)
            elif phase == "rebirth":
                compressed = re.sub(r"([aeiouAEIOU])", "", text)
                out = f"{compressed}\n\n⟁ SONG-BIRTH ⟁"
            elif phase == "peak":
                out = text.upper()
            else:
                words = text.split()
                expanded = []
                for i, w in enumerate(words):
                    expanded.append(w)
                    if i % 7 == 0:
                        expanded.append("mythic")
                out = " ".join(expanded)
            return DriftResult(out, {"event": event_type, "phase": phase, "before_chars": before_chars, "after_chars": len(out)})

        if event_type == "glyph_fusion":
            left = str(event_payload.get("left", "A"))
            right = str(event_payload.get("right", "E"))
            fused = str(event_payload.get("fused", "Æ"))
            pair = f"{left}{right}"
            count = text.count(pair)
            out = text.replace(pair, fused)
            return DriftResult(out, {"event": event_type, "fusions": count, "pair": pair, "fused": fused, "before_chars": before_chars, "after_chars": len(out)})

        return DriftResult(text, {"event": event_type, "before_chars": before_chars, "after_chars": len(text), "note": "no-op"})

    def _compress_snapshot(self, snapshot: dict[str, Any]) -> str:
        encoded = json.dumps(snapshot, sort_keys=True).encode("utf-8")
        compressed = zlib.compress(encoded, level=9)
        return base64.b64encode(compressed).decode("ascii")

    def _simple_distance(self, left: str, right: str) -> int:
        length = max(len(left), len(right))
        distance = 0
        for idx in range(length):
            l = left[idx] if idx < len(left) else ""
            r = right[idx] if idx < len(right) else ""
            if l != r:
                distance += 1
        return distance
