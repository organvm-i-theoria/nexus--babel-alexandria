"""Remix/recombination engine for ARC4N Living Digital Canon."""

from __future__ import annotations

import hashlib
import json
import random
import re
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from nexus_babel.models import Atom, Branch, BranchEvent, Document, RemixArtifact, RemixSourceLink
from nexus_babel.services.evolution import EvolutionService
from nexus_babel.services.governance import GovernanceService


class RemixService:
    def __init__(self, evolution_service: EvolutionService, governance_service: GovernanceService | None = None):
        self.evolution = evolution_service
        self.governance = governance_service

    def remix(
        self,
        session: Session,
        source_document_id: str | None,
        source_branch_id: str | None,
        target_document_id: str | None,
        target_branch_id: str | None,
        strategy: str,
        seed: int,
        mode: str,
    ) -> tuple[Branch, BranchEvent]:
        result = self.compose(
            session=session,
            source_document_id=source_document_id,
            source_branch_id=source_branch_id,
            target_document_id=target_document_id,
            target_branch_id=target_branch_id,
            strategy=strategy,
            seed=seed,
            mode=mode,
            atom_levels=[],
            create_branch=True,
            persist_artifact=False,
        )
        branch = result.get("branch")
        event = result.get("event")
        if not isinstance(branch, Branch) or not isinstance(event, BranchEvent):  # pragma: no cover - defensive
            raise RuntimeError("Legacy remix flow expected branch + event result")
        return branch, event

    def compose(
        self,
        *,
        session: Session,
        source_document_id: str | None,
        source_branch_id: str | None,
        target_document_id: str | None,
        target_branch_id: str | None,
        strategy: str,
        seed: int,
        mode: str,
        atom_levels: list[str] | None = None,
        create_branch: bool = True,
        persist_artifact: bool = True,
    ) -> dict[str, Any]:
        source_ctx = self._resolve_context(
            session=session,
            role="source",
            document_id=source_document_id,
            branch_id=source_branch_id,
            atom_levels=atom_levels or [],
        )
        target_ctx = self._resolve_context(
            session=session,
            role="target",
            document_id=target_document_id,
            branch_id=target_branch_id,
            atom_levels=atom_levels or [],
        )

        source_text = source_ctx["text"]
        target_text = target_ctx["text"]
        if not source_text or not target_text:
            raise ValueError("Both source and target must resolve to non-empty text")

        seed_input = (
            f"remix:{strategy}:{seed}:"
            f"{hashlib.sha256(source_text.encode('utf-8')).hexdigest()}:"
            f"{hashlib.sha256(target_text.encode('utf-8')).hexdigest()}:"
            f"{','.join(atom_levels or [])}"
        )
        rng_seed_hex = hashlib.sha256(seed_input.encode("utf-8")).hexdigest()
        rng = random.Random(int(rng_seed_hex, 16) % (2**32))

        remixed, source_atom_refs = self._compose_text(
            source_text=source_text,
            target_text=target_text,
            strategy=strategy,
            rng=rng,
            source_ctx=source_ctx,
            target_ctx=target_ctx,
            atom_levels=atom_levels or [],
        )
        text_hash = hashlib.sha256(remixed.encode("utf-8")).hexdigest()
        payload_hash = hashlib.sha256(
            json.dumps(
                {
                    "strategy": strategy,
                    "seed": int(seed),
                    "mode": mode.upper(),
                    "source_document_id": source_document_id,
                    "source_branch_id": source_branch_id,
                    "target_document_id": target_document_id,
                    "target_branch_id": target_branch_id,
                    "atom_levels": atom_levels or [],
                    "text_hash": text_hash,
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()

        governance_result: dict[str, Any] = {}
        governance_decision_id: str | None = None
        if self.governance is not None:
            governance_result = self.governance.evaluate(session=session, candidate_output=remixed, mode=mode)
            governance_decision_id = governance_result.get("decision_id")

        artifact: RemixArtifact | None = None
        if persist_artifact:
            artifact = self._create_artifact(
                session=session,
                strategy=strategy,
                seed=int(seed),
                mode=mode,
                remixed_text=remixed,
                text_hash=text_hash,
                rng_seed_hex=rng_seed_hex,
                payload_hash=payload_hash,
                create_branch=create_branch,
                governance_decision_id=governance_decision_id,
                governance_trace=(governance_result.get("decision_trace") or {}),
                source_ctx=source_ctx,
                target_ctx=target_ctx,
                source_atom_refs=source_atom_refs,
            )

        branch: Branch | None = None
        event: BranchEvent | None = None
        if create_branch:
            root_doc_id = source_document_id or source_ctx.get("root_document_id")
            branch, event = self.evolution.evolve_branch(
                session=session,
                parent_branch_id=source_branch_id,
                root_document_id=root_doc_id,
                event_type="remix",
                event_payload={
                    "seed": int(seed),
                    "strategy": strategy,
                    "remixed_text": remixed,
                    "remix_payload_hash": payload_hash,
                    "source_document_id": source_document_id,
                    "target_document_id": target_document_id,
                    "source_branch_id": source_branch_id,
                    "target_branch_id": target_branch_id,
                    "atom_levels": atom_levels or [],
                    "remix_artifact_id": artifact.id if artifact else None,
                },
                mode=mode,
            )
            if artifact is not None:
                artifact.branch_id = branch.id
                artifact.branch_event_id = event.id
                artifact.lineage_graph_refs = self._build_lineage_graph_refs(
                    source_ctx=source_ctx,
                    target_ctx=target_ctx,
                    branch_id=branch.id,
                    branch_event_id=event.id,
                    remix_artifact_id=artifact.id,
                )
        elif artifact is not None:
            artifact.lineage_graph_refs = self._build_lineage_graph_refs(
                source_ctx=source_ctx,
                target_ctx=target_ctx,
                branch_id=None,
                branch_event_id=None,
                remix_artifact_id=artifact.id,
            )

        return {
            "strategy": strategy,
            "seed": int(seed),
            "mode": mode.upper(),
            "remixed_text": remixed,
            "text_hash": text_hash,
            "payload_hash": payload_hash,
            "rng_seed_hex": rng_seed_hex,
            "source_atom_refs": source_atom_refs,
            "remix_artifact": artifact,
            "governance_result": governance_result,
            "branch": branch,
            "event": event,
        }

    def get_remix_artifact(self, session: Session, remix_artifact_id: str) -> dict[str, Any]:
        artifact = session.scalar(select(RemixArtifact).where(RemixArtifact.id == remix_artifact_id))
        if not artifact:
            raise LookupError(f"Remix artifact {remix_artifact_id} not found")
        return self._artifact_to_dict(artifact)

    def list_remix_artifacts(self, session: Session, *, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        total = int(session.scalar(select(func.count(RemixArtifact.id))) or 0)
        artifacts = session.scalars(
            select(RemixArtifact).order_by(RemixArtifact.created_at.desc(), RemixArtifact.id.desc()).offset(offset).limit(limit)
        ).all()
        return {
            "items": [self._artifact_summary(a) for a in artifacts],
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    def _artifact_summary(self, artifact: RemixArtifact) -> dict[str, Any]:
        return {
            "remix_artifact_id": artifact.id,
            "strategy": artifact.strategy,
            "seed": artifact.seed,
            "mode": artifact.mode,
            "text_hash": artifact.text_hash,
            "create_branch": artifact.create_branch,
            "branch_id": artifact.branch_id,
            "governance_decision_id": artifact.governance_decision_id,
            "source_document_id": artifact.source_document_id,
            "target_document_id": artifact.target_document_id,
            "created_at": artifact.created_at,
        }

    def _artifact_to_dict(self, artifact: RemixArtifact) -> dict[str, Any]:
        source_links = sorted(list(artifact.source_links or []), key=lambda r: (r.role, r.id))
        governance_trace = ((artifact.artifact_metadata or {}).get("governance") or {}).get("decision_trace") or {}
        return {
            "remix_artifact_id": artifact.id,
            "strategy": artifact.strategy,
            "seed": artifact.seed,
            "mode": artifact.mode,
            "remixed_text": artifact.remixed_text,
            "text_hash": artifact.text_hash,
            "payload_hash": artifact.payload_hash,
            "rng_seed_hex": artifact.rng_seed_hex,
            "create_branch": artifact.create_branch,
            "source_document_id": artifact.source_document_id,
            "source_branch_id": artifact.source_branch_id,
            "target_document_id": artifact.target_document_id,
            "target_branch_id": artifact.target_branch_id,
            "branch_id": artifact.branch_id,
            "branch_event_id": artifact.branch_event_id,
            "governance_decision_id": artifact.governance_decision_id,
            "governance_trace": governance_trace,
            "lineage_graph_refs": artifact.lineage_graph_refs or {},
            "source_links": [
                {
                    "role": row.role,
                    "document_id": row.document_id,
                    "branch_id": row.branch_id,
                    "atom_level": row.atom_level,
                    "atom_count": row.atom_count,
                    "atom_refs": row.atom_refs or [],
                }
                for row in source_links
            ],
            "created_at": artifact.created_at,
        }

    def _resolve_context(
        self,
        *,
        session: Session,
        role: str,
        document_id: str | None,
        branch_id: str | None,
        atom_levels: list[str],
    ) -> dict[str, Any]:
        text = ""
        root_document_id: str | None = None
        branch: Branch | None = None
        document: Document | None = None
        if branch_id:
            branch = session.scalar(select(Branch).where(Branch.id == branch_id))
            if not branch:
                raise LookupError(f"{role} branch {branch_id} not found")
            text = str((branch.state_snapshot or {}).get("current_text", ""))
            root_document_id = branch.root_document_id
        if document_id:
            document = session.scalar(select(Document).where(Document.id == document_id))
            if not document:
                raise LookupError(f"{role} document {document_id} not found")
            if not text:
                text = str((document.provenance or {}).get("extracted_text", ""))
            root_document_id = root_document_id or document.id

        atoms_by_level: dict[str, list[Atom]] = {}
        if document and atom_levels:
            atoms = session.scalars(
                select(Atom)
                .where(Atom.document_id == document.id, Atom.atom_level.in_(atom_levels))
                .order_by(Atom.atom_level, Atom.ordinal, Atom.id)
            ).all()
            for atom in atoms:
                atoms_by_level.setdefault(atom.atom_level, []).append(atom)

        return {
            "role": role,
            "document_id": document_id,
            "branch_id": branch_id,
            "root_document_id": root_document_id,
            "text": text,
            "atoms_by_level": atoms_by_level,
        }

    def _compose_text(
        self,
        *,
        source_text: str,
        target_text: str,
        strategy: str,
        rng: random.Random,
        source_ctx: dict[str, Any],
        target_ctx: dict[str, Any],
        atom_levels: list[str],
    ) -> tuple[str, list[dict[str, Any]]]:
        source_atom_refs: list[dict[str, Any]] = []
        target_atom_refs: list[dict[str, Any]] = []
        if atom_levels:
            preferred = self._preferred_levels_for_strategy(strategy)
            selected_source = self._pick_atom_level(source_ctx.get("atoms_by_level", {}), preferred)
            selected_target = self._pick_atom_level(target_ctx.get("atoms_by_level", {}), preferred)
            if selected_source and selected_target:
                source_atoms = source_ctx["atoms_by_level"][selected_source]
                target_atoms = target_ctx["atoms_by_level"][selected_target]
                source_text = self._join_atoms_for_strategy(source_atoms, selected_source)
                target_text = self._join_atoms_for_strategy(target_atoms, selected_target)
                source_atom_refs = [
                    {"atom_id": a.id, "atom_level": a.atom_level, "ordinal": a.ordinal, "role": "source"}
                    for a in source_atoms
                ]
                target_atom_refs = [
                    {"atom_id": a.id, "atom_level": a.atom_level, "ordinal": a.ordinal, "role": "target"}
                    for a in target_atoms
                ]

        remixed = self._apply_strategy(source_text, target_text, strategy, rng)
        return remixed, source_atom_refs + target_atom_refs

    def _preferred_levels_for_strategy(self, strategy: str) -> list[str]:
        if strategy == "thematic_blend":
            return ["sentence", "word", "paragraph", "glyph-seed", "syllable"]
        if strategy == "temporal_layer":
            return ["paragraph", "sentence", "word", "glyph-seed", "syllable"]
        if strategy == "glyph_collide":
            return ["glyph-seed", "word", "syllable", "sentence", "paragraph"]
        return ["word", "sentence", "paragraph", "glyph-seed", "syllable"]

    def _pick_atom_level(self, atoms_by_level: dict[str, list[Atom]], preferred_levels: list[str]) -> str | None:
        for level in preferred_levels:
            if atoms_by_level.get(level):
                return level
        return None

    def _join_atoms_for_strategy(self, atoms: list[Atom], atom_level: str) -> str:
        if atom_level == "paragraph":
            return "\n\n".join(a.content for a in atoms)
        if atom_level == "sentence":
            return " ".join(a.content for a in atoms)
        if atom_level == "glyph-seed":
            return "".join(a.content for a in atoms)
        return " ".join(a.content for a in atoms)

    def _create_artifact(
        self,
        *,
        session: Session,
        strategy: str,
        seed: int,
        mode: str,
        remixed_text: str,
        text_hash: str,
        rng_seed_hex: str,
        payload_hash: str,
        create_branch: bool,
        governance_decision_id: str | None,
        governance_trace: dict[str, Any],
        source_ctx: dict[str, Any],
        target_ctx: dict[str, Any],
        source_atom_refs: list[dict[str, Any]],
    ) -> RemixArtifact:
        artifact = RemixArtifact(
            source_document_id=source_ctx.get("document_id"),
            source_branch_id=source_ctx.get("branch_id"),
            target_document_id=target_ctx.get("document_id"),
            target_branch_id=target_ctx.get("branch_id"),
            strategy=strategy,
            seed=seed,
            mode=mode.upper(),
            remixed_text=remixed_text,
            text_hash=text_hash,
            rng_seed_hex=rng_seed_hex,
            payload_hash=payload_hash,
            create_branch=create_branch,
            governance_decision_id=governance_decision_id,
            artifact_metadata={"governance": {"decision_trace": governance_trace}},
        )
        session.add(artifact)
        session.flush()

        source_refs = [row for row in source_atom_refs if row.get("role") == "source"]
        target_refs = [row for row in source_atom_refs if row.get("role") == "target"]
        source_level = source_refs[0]["atom_level"] if source_refs else None
        target_level = target_refs[0]["atom_level"] if target_refs else None

        session.add_all(
            [
                RemixSourceLink(
                    remix_artifact_id=artifact.id,
                    role="source",
                    document_id=source_ctx.get("document_id"),
                    branch_id=source_ctx.get("branch_id"),
                    atom_level=source_level,
                    atom_count=len(source_refs),
                    atom_refs=source_refs,
                ),
                RemixSourceLink(
                    remix_artifact_id=artifact.id,
                    role="target",
                    document_id=target_ctx.get("document_id"),
                    branch_id=target_ctx.get("branch_id"),
                    atom_level=target_level,
                    atom_count=len(target_refs),
                    atom_refs=target_refs,
                ),
            ]
        )
        session.flush()
        return artifact

    def _build_lineage_graph_refs(
        self,
        *,
        source_ctx: dict[str, Any],
        target_ctx: dict[str, Any],
        branch_id: str | None,
        branch_event_id: str | None,
        remix_artifact_id: str,
    ) -> dict[str, Any]:
        nodes: list[str] = [f"remix:{remix_artifact_id}"]
        for key in ("document_id", "branch_id"):
            if source_ctx.get(key):
                nodes.append(f"source_{key}:{source_ctx[key]}")
            if target_ctx.get(key):
                nodes.append(f"target_{key}:{target_ctx[key]}")
        if branch_id:
            nodes.append(f"branch:{branch_id}")
        if branch_event_id:
            nodes.append(f"branch_event:{branch_event_id}")
        return {
            "nodes": nodes,
            "edges": [
                {"from": f"remix:{remix_artifact_id}", "to": f"branch:{branch_id}", "type": "PRODUCED"}
                for _ in [1]
                if branch_id
            ],
        }

    def _resolve_text(self, session: Session, document_id: str | None, branch_id: str | None) -> str:
        if branch_id:
            branch = session.scalar(select(Branch).where(Branch.id == branch_id))
            if branch:
                return str((branch.state_snapshot or {}).get("current_text", ""))
        if document_id:
            doc = session.scalar(select(Document).where(Document.id == document_id))
            if doc:
                return str((doc.provenance or {}).get("extracted_text", ""))
        return ""

    def _branch_root_doc(self, session: Session, branch_id: str) -> str | None:
        branch = session.scalar(select(Branch).where(Branch.id == branch_id))
        return branch.root_document_id if branch else None

    def _apply_strategy(self, source: str, target: str, strategy: str, rng: random.Random) -> str:
        if strategy == "interleave":
            return self._interleave(source, target)
        if strategy == "thematic_blend":
            return self._thematic_blend(source, target, rng)
        if strategy == "temporal_layer":
            return self._temporal_layer(source, target, rng)
        if strategy == "glyph_collide":
            return self._glyph_collide(source, target, rng)
        raise ValueError(f"Unknown remix strategy: {strategy}")

    def _interleave(self, source: str, target: str) -> str:
        source_words = re.findall(r"\S+", source)
        target_words = re.findall(r"\S+", target)
        result: list[str] = []
        max_len = max(len(source_words), len(target_words))
        for i in range(max_len):
            if i < len(source_words):
                result.append(source_words[i])
            if i < len(target_words):
                result.append(target_words[i])
        return " ".join(result)

    def _thematic_blend(self, source: str, target: str, rng: random.Random) -> str:
        source_sentences = [s.strip() for s in re.split(r"[.!?]+", source) if s.strip()]
        target_sentences = [s.strip() for s in re.split(r"[.!?]+", target) if s.strip()]
        combined = source_sentences + target_sentences
        rng.shuffle(combined)
        if not combined:
            return ""
        return ". ".join(combined[: max(len(source_sentences), len(target_sentences), 1)]) + "."

    def _temporal_layer(self, source: str, target: str, rng: random.Random) -> str:
        source_paras = [p.strip() for p in re.split(r"\n\s*\n", source) if p.strip()]
        target_paras = [p.strip() for p in re.split(r"\n\s*\n", target) if p.strip()]
        result: list[str] = []
        max_len = max(len(source_paras), len(target_paras), 1)
        for i in range(max_len):
            if i < len(source_paras):
                result.append(source_paras[i])
            if i < len(target_paras) and rng.random() > 0.3:
                result.append(f"[temporal overlay] {target_paras[i]}")
        return "\n\n".join(result)

    def _glyph_collide(self, source: str, target: str, rng: random.Random) -> str:
        source_glyphs = [c for c in source if not c.isspace()]
        target_glyphs = [c for c in target if not c.isspace()]
        result: list[str] = []
        max_len = max(len(source_glyphs), len(target_glyphs))
        for i in range(min(max_len, 2000)):
            s = source_glyphs[i] if i < len(source_glyphs) else ""
            t = target_glyphs[i] if i < len(target_glyphs) else ""
            if s == t:
                result.append(s)
            elif s and t:
                result.append(s if rng.random() > 0.5 else t)
            else:
                result.append(s or t)
        return "".join(result)

