from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from nexus_babel.models import Document, DocumentVariant


def _normalize_stem(path: str) -> str:
    stem = Path(path).stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return stem


def apply_canonicalization(session: Session, documents: list[Document]) -> None:
    document_ids = [d.id for d in documents]
    if not document_ids:
        return

    session.execute(delete(DocumentVariant).where(DocumentVariant.document_id.in_(document_ids)))

    # Known semantic equivalence group for duplicated long-form RLOS specs.
    semantic_group = []
    for doc in documents:
        p = doc.path.lower()
        if "theoria linguae machina comprehensive design document" in p or "nexus_bable-alexandria" in p:
            semantic_group.append(doc)

    for doc in semantic_group:
        session.add(
            DocumentVariant(
                document_id=doc.id,
                variant_group="rlos_spec_v1_equivalent",
                variant_type="semantic_equivalence",
                related_document_id=None,
            )
        )

    # Pair sibling representations by normalized stem across extensions.
    groups: dict[str, list[Document]] = defaultdict(list)
    for doc in documents:
        groups[_normalize_stem(doc.path)].append(doc)

    for group_name, group_docs in groups.items():
        if len(group_docs) < 2:
            continue
        group_id = f"sibling::{group_name}"
        for doc in group_docs:
            for related in group_docs:
                if related.id == doc.id:
                    continue
                session.add(
                    DocumentVariant(
                        document_id=doc.id,
                        variant_group=group_id,
                        variant_type="sibling_representation",
                        related_document_id=related.id,
                    )
                )


def collect_current_corpus_paths(root: Path) -> list[Path]:
    supported = {
        ".md",
        ".pdf",
        ".txt",
        ".yaml",
        ".yml",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".wav",
        ".mp3",
        ".flac",
    }
    paths: list[Path] = []
    for child in sorted(root.iterdir()):
        if not child.is_file():
            continue
        if child.name.startswith("."):
            continue
        if child.suffix.lower() in supported:
            paths.append(child)
    return paths


def get_document_text(session: Session, document_id: str) -> str:
    doc = session.scalar(select(Document).where(Document.id == document_id))
    if not doc:
        return ""
    return str((doc.provenance or {}).get("extracted_text", ""))
