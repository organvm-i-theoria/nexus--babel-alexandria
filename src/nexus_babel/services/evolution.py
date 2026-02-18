from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_babel.models import Branch, BranchEvent, Document


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

    def evolve_branch(
        self,
        session: Session,
        parent_branch_id: str | None,
        root_document_id: str | None,
        event_type: str,
        event_payload: dict[str, Any],
        mode: str,
    ) -> tuple[Branch, BranchEvent]:
        parent = None
        if parent_branch_id:
            parent = session.scalar(select(Branch).where(Branch.id == parent_branch_id))
            if not parent:
                raise ValueError(f"Parent branch {parent_branch_id} not found")
            root_document_id = parent.root_document_id
            base_text = str((parent.state_snapshot or {}).get("current_text", ""))
        else:
            if not root_document_id:
                raise ValueError("root_document_id is required when parent_branch_id is not provided")
            doc = session.scalar(select(Document).where(Document.id == root_document_id))
            if not doc:
                raise ValueError(f"Root document {root_document_id} not found")
            base_text = str((doc.provenance or {}).get("extracted_text", ""))

        drift = self._apply_event(base_text, event_type=event_type, event_payload=event_payload)

        new_branch = Branch(
            parent_branch_id=parent.id if parent else None,
            root_document_id=root_document_id,
            name=f"branch-{event_type}",
            mode=mode.upper(),
            state_snapshot={
                "current_text": drift.output_text,
                "phase": event_payload.get("phase", "expansion"),
                "text_hash": hashlib.sha256(drift.output_text.encode("utf-8")).hexdigest(),
            },
        )
        session.add(new_branch)
        session.flush()

        event = BranchEvent(
            branch_id=new_branch.id,
            event_index=1,
            event_type=event_type,
            event_payload=event_payload,
            diff_summary=drift.diff_summary,
            result_snapshot={
                "text_hash": hashlib.sha256(drift.output_text.encode("utf-8")).hexdigest(),
                "preview": drift.output_text[:500],
            },
        )
        session.add(event)

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
            },
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
