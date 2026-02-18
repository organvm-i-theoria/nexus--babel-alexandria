from __future__ import annotations

import statistics
from collections import Counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_babel.models import AnalysisRun, Branch, Document
from nexus_babel.services.rhetoric import RhetoricalAnalyzer
from nexus_babel.services.text_utils import split_paragraphs, split_sentences, tokenize_words


class AnalysisService:
    def __init__(self, rhetorical_analyzer: RhetoricalAnalyzer):
        self.rhetorical_analyzer = rhetorical_analyzer

    def analyze(
        self,
        session: Session,
        document_id: str | None,
        branch_id: str | None,
        layers: list[str],
        mode: str,
    ) -> tuple[AnalysisRun, dict[str, Any]]:
        text = ""
        hypergraph_ids: dict[str, Any] = {}

        if document_id:
            doc = session.scalar(select(Document).where(Document.id == document_id))
            if not doc:
                raise ValueError(f"document_id {document_id} not found")
            text = str((doc.provenance or {}).get("extracted_text", ""))
            hypergraph_ids = (doc.provenance or {}).get("hypergraph", {})
        elif branch_id:
            branch = session.scalar(select(Branch).where(Branch.id == branch_id))
            if not branch:
                raise ValueError(f"branch_id {branch_id} not found")
            text = str((branch.state_snapshot or {}).get("current_text", ""))
            hypergraph_ids = {"branch_id": branch.id}
        else:
            raise ValueError("Either document_id or branch_id must be provided")

        requested = layers or [
            "token",
            "morphology",
            "syntax",
            "semantics",
            "pragmatics",
            "discourse",
            "sociolinguistics",
            "rhetoric",
            "semiotic",
        ]

        words = tokenize_words(text)
        sentences = split_sentences(text)
        paragraphs = split_paragraphs(text)
        word_lengths = [len(w) for w in words] or [0]

        entity_candidates = [w for w in words if len(w) > 1 and w[0].isupper()]
        top_entities = [token for token, _ in Counter(entity_candidates).most_common(10)]

        rhetorical = self.rhetorical_analyzer.analyze(text)

        layer_outputs: dict[str, Any] = {
            "token": {
                "token_count": len(words),
                "unique_tokens": len(set(map(str.lower, words))),
            },
            "morphology": {
                "avg_word_length": round(statistics.mean(word_lengths), 3),
                "long_word_ratio": round(sum(1 for w in words if len(w) >= 8) / max(1, len(words)), 3),
            },
            "syntax": {
                "sentence_count": len(sentences),
                "avg_sentence_length": round(sum(len(tokenize_words(s)) for s in sentences) / max(1, len(sentences)), 3),
            },
            "semantics": {
                "named_entities": top_entities,
                "semantic_density": round(len(set(map(str.lower, words))) / max(1, len(words)), 3),
            },
            "pragmatics": {
                "question_count": text.count("?"),
                "exclamation_count": text.count("!"),
                "hedge_count": sum(text.lower().count(h) for h in ["maybe", "perhaps", "likely", "possibly"]),
            },
            "discourse": {
                "paragraph_count": len(paragraphs),
                "connective_count": sum(text.lower().count(c) for c in ["however", "therefore", "because", "although"]),
            },
            "sociolinguistics": {
                "contraction_count": sum(text.count(c) for c in ["n't", "'re", "'ll", "'ve"]),
                "formality_score": round(1.0 - (text.count("!") / max(1, len(sentences))), 3),
            },
            "rhetoric": rhetorical,
            "semiotic": {
                "emoji_count": sum(1 for ch in text if ord(ch) > 10000),
                "glyph_count": sum(1 for ch in text if ch in {"∆", "Æ", "Ω", "☲", "⟁", "Λ", "@"}),
                "symbol_density": round(sum(1 for ch in text if not ch.isalnum() and not ch.isspace()) / max(1, len(text)), 4),
            },
        }

        selected_outputs = {layer: layer_outputs.get(layer, {}) for layer in requested}
        confidence = {layer: 0.65 if selected_outputs[layer] else 0.0 for layer in selected_outputs}

        run = AnalysisRun(
            document_id=document_id,
            branch_id=branch_id,
            mode=mode.upper(),
            layers=requested,
            confidence=confidence,
            results=selected_outputs,
        )
        session.add(run)

        return run, {
            "mode": mode.upper(),
            "layers": selected_outputs,
            "confidence_bundle": confidence,
            "hypergraph_ids": hypergraph_ids,
        }
