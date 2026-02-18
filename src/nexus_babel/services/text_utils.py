from __future__ import annotations

import hashlib
import re
from pathlib import Path


WORD_PATTERN = re.compile(r"[\w'-]+", flags=re.UNICODE)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
PARAGRAPH_SPLIT = re.compile(r"\n\s*\n+")
CONFLICT_MARKER = re.compile(r"^(<<<<<<<|=======|>>>>>>>|\|\|\|\|\|\|\|)", flags=re.MULTILINE)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


def has_conflict_markers(text: str) -> bool:
    return bool(CONFLICT_MARKER.search(text))


def atomize_text(text: str) -> dict[str, list[str]]:
    glyphs = [c for c in text if not c.isspace()]
    words = WORD_PATTERN.findall(text)
    sentences = [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]
    paragraphs = [p.strip() for p in PARAGRAPH_SPLIT.split(text) if p.strip()]
    return {
        "glyph-seed": glyphs,
        "word": words,
        "sentence": sentences,
        "paragraph": paragraphs,
    }


def tokenize_words(text: str) -> list[str]:
    return WORD_PATTERN.findall(text)


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in PARAGRAPH_SPLIT.split(text) if p.strip()]
