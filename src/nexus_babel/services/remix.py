"""Remix/recombination engine for ARC4N Living Digital Canon.

Recombines atoms across documents using deterministic strategies:
- interleave: alternate atoms from two sources
- thematic_blend: match atoms by thematic tags and merge
- temporal_layer: overlay one text's timeline onto another's
- glyph_collide: fuse glyph-seeds where they overlap
"""

from __future__ import annotations

import hashlib
import random
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_babel.models import Branch, BranchEvent, Document
from nexus_babel.services.evolution import EvolutionService


class RemixService:
    def __init__(self, evolution_service: EvolutionService):
        self.evolution = evolution_service

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
        source_text = self._resolve_text(session, source_document_id, source_branch_id)
        target_text = self._resolve_text(session, target_document_id, target_branch_id)

        if not source_text or not target_text:
            raise ValueError("Both source and target must resolve to non-empty text")

        seed_input = f"remix:{strategy}:{seed}:{hashlib.sha256(source_text.encode()).hexdigest()}:{hashlib.sha256(target_text.encode()).hexdigest()}"
        rng = random.Random(int(hashlib.sha256(seed_input.encode()).hexdigest(), 16) % (2**32))

        remixed = self._apply_strategy(source_text, target_text, strategy, rng)

        root_doc_id = source_document_id or (
            self._branch_root_doc(session, source_branch_id) if source_branch_id else None
        )

        return self.evolution.evolve_branch(
            session=session,
            parent_branch_id=source_branch_id,
            root_document_id=root_doc_id,
            event_type="remix",
            event_payload={
                "seed": seed,
                "strategy": strategy,
                "remixed_text": remixed,
                "source_document_id": source_document_id,
                "target_document_id": target_document_id,
                "source_branch_id": source_branch_id,
                "target_branch_id": target_branch_id,
            },
            mode=mode,
        )

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
        return ". ".join(combined[:max(len(source_sentences), len(target_sentences))]) + "."

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
