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
        # Original 5
        "th": "þ",
        "ae": "æ",
        "ph": "f",
        "ck": "k",
        "tion": "cion",
        # Latin → Italian
        "ct": "tt",
        "pl": "pi",
        "fl": "fi",
        "cl": "chi",
        "x": "ss",
        "li": "gli",
        "ni": "gn",
        # Old English → Modern English
        "sc": "sh",
        "cw": "qu",
        "hw": "wh",
        # Great Vowel Shift approximations
        "oo": "ou",
        "ee": "ea",
        "igh": "eye",
        # Common phonetic drifts
        "ght": "t",
        "ough": "ow",
        "wh": "w",
        "kn": "n",
        "wr": "r",
        "mb": "m",
        "gn": "n",
    }

    REVERSE_NATURAL_MAP = {
        "þ": "th",
        "æ": "ae",
        "f": "ph",
        "k": "ck",
        "cion": "tion",
        "tt": "ct",
        "pi": "pl",
        "fi": "fl",
        "chi": "cl",
        "ss": "x",
        "sh": "sc",
        "qu": "cw",
    }

    GLYPH_POOL = ["∆", "Æ", "Ω", "§", "☲", "⟁", "Ψ", "Φ", "Θ", "Ξ"]
    PHASES = {"expansion", "peak", "compression", "rebirth"}
    MERGE_STRATEGIES = {"left_wins", "right_wins", "interleave"}

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
        session.flush()

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

    def multi_evolve(
        self,
        session: Session,
        parent_branch_id: str | None,
        root_document_id: str | None,
        events: list[dict[str, Any]],
        mode: str,
    ) -> dict[str, Any]:
        if not events:
            raise ValueError("events must not be empty")

        created_pairs: list[tuple[Branch, BranchEvent]] = []
        current_parent_branch_id = parent_branch_id
        current_root_document_id = root_document_id

        for idx, item in enumerate(events):
            event_type = str((item or {}).get("event_type", "")).strip()
            event_payload = dict((item or {}).get("event_payload") or {})
            if not event_type:
                raise ValueError(f"events[{idx}].event_type is required")

            branch, event = self.evolve_branch(
                session=session,
                parent_branch_id=current_parent_branch_id,
                root_document_id=current_root_document_id,
                event_type=event_type,
                event_payload=event_payload,
                mode=mode,
            )
            created_pairs.append((branch, event))
            current_parent_branch_id = branch.id
            current_root_document_id = branch.root_document_id

        final_branch = created_pairs[-1][0]
        final_snapshot = dict(final_branch.state_snapshot or {})
        final_text = str(final_snapshot.get("current_text", ""))
        final_text_hash = str(final_snapshot.get("text_hash") or hashlib.sha256(final_text.encode("utf-8")).hexdigest())

        return {
            "branches": [branch for branch, _ in created_pairs],
            "events": [event for _, event in created_pairs],
            "branch_ids": [branch.id for branch, _ in created_pairs],
            "event_ids": [event.id for _, event in created_pairs],
            "final_branch_id": final_branch.id,
            "event_count": len(created_pairs),
            "final_text_hash": final_text_hash,
            "final_preview": final_text[:500],
        }

    def merge_branches(
        self,
        session: Session,
        left_branch_id: str,
        right_branch_id: str,
        strategy: str,
        *,
        mode: str = "PUBLIC",
    ) -> tuple[Branch, BranchEvent, Branch | None]:
        left_branch = session.scalar(select(Branch).where(Branch.id == left_branch_id))
        if not left_branch:
            raise LookupError(f"Left branch {left_branch_id} not found")
        right_branch = session.scalar(select(Branch).where(Branch.id == right_branch_id))
        if not right_branch:
            raise LookupError(f"Right branch {right_branch_id} not found")

        normalized_strategy = str(strategy).strip().lower()
        if normalized_strategy not in self.MERGE_STRATEGIES:
            raise ValueError(f"Unsupported merge strategy: {strategy}")

        lca = self._find_lca(session, left_branch, right_branch)
        if lca is None and left_branch.root_document_id != right_branch.root_document_id:
            raise ValueError("Branches do not share a common ancestor or root document")

        left_text, _, _ = self._replay_lineage_text(session, left_branch, use_checkpoints=True)
        right_text, _, _ = self._replay_lineage_text(session, right_branch, use_checkpoints=True)
        merged_text = self._merge_texts(left_text, right_text, normalized_strategy)
        conflict_semantics = self._build_merge_conflict_semantics(
            left_text=left_text,
            right_text=right_text,
            merged_text=merged_text,
            strategy=normalized_strategy,
        )

        merge_payload = {
            "strategy": normalized_strategy,
            "left_branch_id": left_branch_id,
            "right_branch_id": right_branch_id,
            "lca_branch_id": getattr(lca, "id", None),
            "merged_text": merged_text,
            "left_text_hash": hashlib.sha256(left_text.encode("utf-8")).hexdigest(),
            "right_text_hash": hashlib.sha256(right_text.encode("utf-8")).hexdigest(),
            "conflict_semantics": conflict_semantics,
            "seed": 0,
        }
        branch, event = self.evolve_branch(
            session=session,
            parent_branch_id=left_branch.id,
            root_document_id=left_branch.root_document_id,
            event_type="merge",
            event_payload=merge_payload,
            mode=mode,
        )
        return branch, event, lca

    def get_timeline(self, session: Session, branch_id: str) -> dict[str, Any]:
        branch = session.scalar(select(Branch).where(Branch.id == branch_id))
        if not branch:
            raise ValueError(f"Branch {branch_id} not found")

        replay_text, lineage, events = self._replay_lineage_text(session, branch, use_checkpoints=True)

        return {
            "branch": branch,
            "events": events,
            "replay_snapshot": {
                "text_hash": hashlib.sha256(replay_text.encode("utf-8")).hexdigest(),
                "preview": replay_text[:500],
                "event_count": len(events),
            },
        }

    def get_visualization(self, session: Session, branch_id: str) -> dict[str, Any]:
        branch = session.scalar(select(Branch).where(Branch.id == branch_id))
        if not branch:
            raise ValueError(f"Branch {branch_id} not found")

        primary_lineage = self._lineage(session, branch)
        primary_branch_ids = {node.id for node in primary_lineage}
        branches_by_id: dict[str, Branch] = {node.id: node for node in primary_lineage}
        branch_events_by_id: dict[str, list[BranchEvent]] = {}
        scan_queue: list[Branch] = list(primary_lineage)
        scanned: set[str] = set()

        # Expand graph to include merge secondary parent lineages so secondary-parent
        # edges point to actual nodes in the graph.
        while scan_queue:
            node = scan_queue.pop(0)
            if node.id in scanned:
                continue
            scanned.add(node.id)
            branch_events = session.scalars(
                select(BranchEvent).where(BranchEvent.branch_id == node.id).order_by(BranchEvent.event_index, BranchEvent.created_at)
            ).all()
            branch_events_by_id[node.id] = branch_events

            for event in branch_events:
                if event.event_type != "merge":
                    continue
                right_branch_id = str((event.event_payload or {}).get("right_branch_id") or "").strip()
                if not right_branch_id:
                    continue
                right_branch = session.scalar(select(Branch).where(Branch.id == right_branch_id))
                if not right_branch:
                    continue
                for secondary_node in self._lineage(session, right_branch):
                    if secondary_node.id not in branches_by_id:
                        branches_by_id[secondary_node.id] = secondary_node
                        scan_queue.append(secondary_node)

        lineage = list(primary_lineage) + sorted(
            [node for node_id, node in branches_by_id.items() if node_id not in primary_branch_ids],
            key=lambda node: (node.created_at, node.id),
        )
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        edge_ids: set[str] = set()
        secondary_branch_ids = {node.id for node in lineage if node.id not in primary_branch_ids}

        for node in lineage:
            branch_events = branch_events_by_id.get(node.id)
            if branch_events is None:
                branch_events = session.scalars(
                    select(BranchEvent).where(BranchEvent.branch_id == node.id).order_by(BranchEvent.event_index, BranchEvent.created_at)
                ).all()
                branch_events_by_id[node.id] = branch_events

            phase = str((node.state_snapshot or {}).get("phase", "")) or None
            for event in branch_events:
                nodes.append(
                    {
                        "id": event.id,
                        "kind": "event",
                        "branch_id": node.id,
                        "lineage_role": "secondary_merge_parent" if node.id in secondary_branch_ids else "primary",
                        "parent_branch_id": node.parent_branch_id,
                        "root_document_id": node.root_document_id,
                        "event_index": event.event_index,
                        "event_type": event.event_type,
                        "phase": phase,
                        "mode": node.mode,
                        "created_at": event.created_at,
                        "metadata": {
                            "diff_summary": event.diff_summary,
                            "event_payload": event.event_payload,
                        },
                    }
                )

            for prev, curr in zip(branch_events, branch_events[1:]):
                edge_id = f"{prev.id}->{curr.id}"
                if edge_id in edge_ids:
                    continue
                edge_ids.add(edge_id)
                edges.append({"id": edge_id, "source": prev.id, "target": curr.id, "type": "intra_branch_sequence", "metadata": {}})

        last_event_by_branch = {branch_id_: events[-1] for branch_id_, events in branch_events_by_id.items() if events}
        for node in lineage:
            if not node.parent_branch_id:
                continue
            parent_event = last_event_by_branch.get(node.parent_branch_id)
            child_event = last_event_by_branch.get(node.id)
            if parent_event is None or child_event is None:
                continue
            edge_id = f"{parent_event.id}->{child_event.id}:parent"
            if edge_id not in edge_ids:
                edge_ids.add(edge_id)
                edges.append(
                    {
                        "id": edge_id,
                        "source": parent_event.id,
                        "target": child_event.id,
                        "type": "parent_branch",
                        "metadata": {"relationship": "primary_parent"},
                    }
                )

        merge_secondary_edge_count = 0
        for node in lineage:
            for event in branch_events_by_id.get(node.id, []):
                if event.event_type != "merge":
                    continue
                payload = dict(event.event_payload or {})
                right_branch_id = str(payload.get("right_branch_id") or "").strip()
                if not right_branch_id:
                    continue
                secondary_parent_event = last_event_by_branch.get(right_branch_id)
                if secondary_parent_event is None:
                    continue
                edge_id = f"{secondary_parent_event.id}->{event.id}:merge-secondary"
                if edge_id in edge_ids:
                    continue
                edge_ids.add(edge_id)
                merge_secondary_edge_count += 1
                edges.append(
                    {
                        "id": edge_id,
                        "source": secondary_parent_event.id,
                        "target": event.id,
                        "type": "merge_secondary_parent",
                        "metadata": {
                            "strategy": payload.get("strategy"),
                            "lca_branch_id": payload.get("lca_branch_id"),
                            "right_branch_id": right_branch_id,
                        },
                    }
                )

        return {
            "branch_id": branch.id,
            "root_document_id": branch.root_document_id,
            "nodes": nodes,
            "edges": edges,
            "summary": {
                "event_count": len(nodes),
                "edge_count": len(edges),
                "lineage_depth": len(primary_lineage),
                "secondary_lineage_branch_count": len(secondary_branch_ids),
                "merge_secondary_edge_count": merge_secondary_edge_count,
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

    def _latest_lineage_checkpoint(self, session: Session, lineage: list[Branch]) -> BranchCheckpoint | None:
        lineage_ids = [node.id for node in lineage]
        if not lineage_ids:
            return None
        return session.scalar(
            select(BranchCheckpoint)
            .where(BranchCheckpoint.branch_id.in_(lineage_ids))
            .order_by(BranchCheckpoint.event_index.desc(), BranchCheckpoint.created_at.desc())
        )

    def _collect_lineage_events(self, session: Session, lineage: list[Branch]) -> list[BranchEvent]:
        events: list[BranchEvent] = []
        for node in lineage:
            events.extend(
                session.scalars(
                    select(BranchEvent)
                    .where(BranchEvent.branch_id == node.id)
                    .order_by(BranchEvent.event_index, BranchEvent.created_at)
                ).all()
            )
        return events

    def _resolve_root_text(self, session: Session, root_document_id: str | None) -> str:
        if not root_document_id:
            return ""
        doc = session.scalar(select(Document).where(Document.id == root_document_id))
        if not doc:
            return ""
        return str((doc.provenance or {}).get("extracted_text", ""))

    def _replay_lineage_text(
        self,
        session: Session,
        branch: Branch,
        *,
        use_checkpoints: bool = True,
    ) -> tuple[str, list[Branch], list[BranchEvent]]:
        lineage = self._lineage(session, branch)
        events = self._collect_lineage_events(session, lineage)
        replay_text = self._resolve_root_text(session, branch.root_document_id)

        checkpoint_start_index = 0
        if use_checkpoints:
            latest_checkpoint = self._latest_lineage_checkpoint(session, lineage)
            if latest_checkpoint is not None:
                snapshot = self._decompress_snapshot(latest_checkpoint.snapshot_compressed)
                if "current_text" in snapshot:
                    replay_text = str(snapshot.get("current_text", ""))
                    checkpoint_start_index = min(max(int(latest_checkpoint.event_index), 0), len(events))

        for event in events[checkpoint_start_index:]:
            replay_text = self._apply_event(replay_text, event.event_type, event.event_payload).output_text

        return replay_text, lineage, events

    def _find_lca(self, session: Session, left_branch: Branch, right_branch: Branch) -> Branch | None:
        left_lineage = self._lineage(session, left_branch)
        right_lineage = self._lineage(session, right_branch)

        left_by_id = {branch.id: branch for branch in left_lineage}
        lca: Branch | None = None
        for branch in right_lineage:
            if branch.id in left_by_id:
                lca = left_by_id[branch.id]
        return lca

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

        if event_type == "remix":
            data.setdefault("seed", 0)
            data.setdefault("strategy", "interleave")
            return data

        if event_type == "reverse_drift":
            data.setdefault("seed", 0)
            return data

        if event_type == "merge":
            strategy = str(data.get("strategy", "interleave")).strip().lower()
            if strategy not in self.MERGE_STRATEGIES:
                raise ValueError(f"Unsupported merge strategy: {strategy}")
            merged_text = str(data.get("merged_text", ""))
            for key in ("left_text_hash", "right_text_hash"):
                if key in data and data[key] is not None:
                    data[key] = str(data[key])
            conflict_semantics = data.get("conflict_semantics", {})
            if not isinstance(conflict_semantics, dict):
                raise ValueError("conflict_semantics must be an object")
            data["strategy"] = strategy
            data["merged_text"] = merged_text
            data["conflict_semantics"] = conflict_semantics
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
            acceleration = float(event_payload.get("acceleration", 1.0))
            phase_order = ["expansion", "peak", "compression", "rebirth"]
            phase_idx = phase_order.index(phase) if phase in phase_order else 0
            # Acceleration multiplier: expansion/peak accelerate, compression/rebirth decelerate
            if phase in ("expansion", "peak"):
                intensity = min(acceleration * (1.0 + phase_idx * 0.5), 5.0)
            else:
                intensity = max(acceleration * (1.0 - (phase_idx - 2) * 0.3), 0.2)

            if phase == "compression":
                # Remove vowels proportional to intensity
                chars = list(text)
                removals = 0
                for i in range(len(chars) - 1, -1, -1):
                    if chars[i].lower() in "aeiou" and rng.random() < min(intensity * 0.6, 1.0):
                        chars.pop(i)
                        removals += 1
                out = "".join(chars)
            elif phase == "rebirth":
                chars = list(text)
                removals = 0
                for i in range(len(chars) - 1, -1, -1):
                    if chars[i].lower() in "aeiou" and rng.random() < min(intensity * 0.4, 1.0):
                        chars.pop(i)
                        removals += 1
                out = f"{''.join(chars)}\n\n⟁ SONG-BIRTH ⟁"
            elif phase == "peak":
                out = text.upper()
                # At high intensity, also expand with mythic insertions
                if intensity > 1.5:
                    words = out.split()
                    expanded = []
                    interval = max(1, int(7 / intensity))
                    for i, w in enumerate(words):
                        expanded.append(w)
                        if i % interval == 0:
                            expanded.append("MYTHIC")
                    out = " ".join(expanded)
            else:
                words = text.split()
                expanded = []
                interval = max(1, int(7 / intensity))
                for i, w in enumerate(words):
                    expanded.append(w)
                    if i % interval == 0:
                        expanded.append("mythic")
                out = " ".join(expanded)
            return DriftResult(out, {"event": event_type, "phase": phase, "acceleration": acceleration, "intensity": intensity, "before_chars": before_chars, "after_chars": len(out)})

        if event_type == "glyph_fusion":
            left = str(event_payload.get("left", "A"))
            right = str(event_payload.get("right", "E"))
            fused = str(event_payload.get("fused", "Æ"))
            pair = f"{left}{right}"
            count = text.count(pair)
            out = text.replace(pair, fused)
            return DriftResult(out, {"event": event_type, "fusions": count, "pair": pair, "fused": fused, "before_chars": before_chars, "after_chars": len(out)})

        if event_type == "remix":
            # Remix events carry pre-computed text from RemixService
            remixed_text = str(event_payload.get("remixed_text", text))
            strategy = str(event_payload.get("strategy", "interleave"))
            return DriftResult(remixed_text, {"event": event_type, "strategy": strategy, "before_chars": before_chars, "after_chars": len(remixed_text)})

        if event_type == "reverse_drift":
            out = text
            reversals = 0
            # Apply longer keys first to avoid short keys (e.g. "f") shadowing
            # more specific reversals (e.g. "fi" -> "fl").
            reverse_pairs = sorted(self.REVERSE_NATURAL_MAP.items(), key=lambda pair: len(pair[0]), reverse=True)
            for old, new in reverse_pairs:
                out, count = re.subn(re.escape(old), new, out, flags=re.IGNORECASE)
                reversals += count
            return DriftResult(
                out,
                {
                    "event": event_type,
                    "reversals": reversals,
                    "before_chars": before_chars,
                    "after_chars": len(out),
                },
            )

        if event_type == "merge":
            merged_text = str(event_payload.get("merged_text", text))
            strategy = str(event_payload.get("strategy", "interleave"))
            conflict_semantics = event_payload.get("conflict_semantics", {})
            if not isinstance(conflict_semantics, dict):
                conflict_semantics = {}
            return DriftResult(
                merged_text,
                {
                    "event": event_type,
                    "strategy": strategy,
                    "left_branch_id": event_payload.get("left_branch_id"),
                    "right_branch_id": event_payload.get("right_branch_id"),
                    "lca_branch_id": event_payload.get("lca_branch_id"),
                    "left_text_hash": event_payload.get("left_text_hash"),
                    "right_text_hash": event_payload.get("right_text_hash"),
                    "conflict_semantics": conflict_semantics,
                    "before_chars": before_chars,
                    "after_chars": len(merged_text),
                },
            )

        return DriftResult(text, {"event": event_type, "before_chars": before_chars, "after_chars": len(text), "note": "no-op"})

    def _compress_snapshot(self, snapshot: dict[str, Any]) -> str:
        encoded = json.dumps(snapshot, sort_keys=True).encode("utf-8")
        compressed = zlib.compress(encoded, level=9)
        return base64.b64encode(compressed).decode("ascii")

    def _decompress_snapshot(self, payload: str) -> dict[str, Any]:
        raw = base64.b64decode(payload.encode("ascii"))
        decoded = zlib.decompress(raw)
        data = json.loads(decoded.decode("utf-8"))
        return data if isinstance(data, dict) else {}

    def _merge_texts(self, left_text: str, right_text: str, strategy: str) -> str:
        if strategy == "left_wins":
            return left_text
        if strategy == "right_wins":
            return right_text
        if strategy == "interleave":
            left_words = left_text.split()
            right_words = right_text.split()
            merged: list[str] = []
            for idx in range(max(len(left_words), len(right_words))):
                if idx < len(left_words):
                    merged.append(left_words[idx])
                if idx < len(right_words):
                    merged.append(right_words[idx])
            return " ".join(merged)
        raise ValueError(f"Unsupported merge strategy: {strategy}")

    def _build_merge_conflict_semantics(
        self,
        *,
        left_text: str,
        right_text: str,
        merged_text: str,
        strategy: str,
    ) -> dict[str, Any]:
        left_words = left_text.split()
        right_words = right_text.split()
        merged_words = merged_text.split()
        left_word_set = set(left_words)
        right_word_set = set(right_words)
        left_hash = hashlib.sha256(left_text.encode("utf-8")).hexdigest()
        right_hash = hashlib.sha256(right_text.encode("utf-8")).hexdigest()
        inputs_identical = left_hash == right_hash

        if inputs_identical:
            resolution = "identical_inputs"
        elif strategy == "left_wins":
            resolution = "left_preferred"
        elif strategy == "right_wins":
            resolution = "right_preferred"
        else:
            resolution = "interleaved_union"

        return {
            "resolution": resolution,
            "strategy_effect": {
                "left_wins": "preserve_left",
                "right_wins": "preserve_right",
                "interleave": "word_interleave",
            }.get(strategy, "unknown"),
            "inputs_identical": inputs_identical,
            "drops_non_selected_input": strategy in {"left_wins", "right_wins"} and not inputs_identical,
            "left_chars": len(left_text),
            "right_chars": len(right_text),
            "merged_chars": len(merged_text),
            "left_words": len(left_words),
            "right_words": len(right_words),
            "merged_words": len(merged_words),
            "shared_word_count": len(left_word_set & right_word_set),
            "left_only_word_count": len(left_word_set - right_word_set),
            "right_only_word_count": len(right_word_set - left_word_set),
            "common_prefix_chars": self._common_prefix_chars(left_text, right_text),
            "common_suffix_chars": self._common_suffix_chars(left_text, right_text),
        }

    def _common_prefix_chars(self, left: str, right: str) -> int:
        count = 0
        for left_char, right_char in zip(left, right):
            if left_char != right_char:
                break
            count += 1
        return count

    def _common_suffix_chars(self, left: str, right: str) -> int:
        count = 0
        for left_char, right_char in zip(reversed(left), reversed(right)):
            if left_char != right_char:
                break
            count += 1
        return count

    def _simple_distance(self, left: str, right: str) -> int:
        length = max(len(left), len(right))
        distance = 0
        for idx in range(length):
            left_char = left[idx] if idx < len(left) else ""
            r = right[idx] if idx < len(right) else ""
            if left_char != r:
                distance += 1
        return distance
