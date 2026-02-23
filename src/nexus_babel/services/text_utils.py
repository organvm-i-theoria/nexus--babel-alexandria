from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path
from typing import Any

from nexus_babel.schemas import GlyphSeed
from nexus_babel.services.glyph_data import (
    get_future_seeds,
    get_historic_forms,
    get_phoneme_hint,
    get_thematic_tags,
    get_visual_mutations,
)


WORD_PATTERN = re.compile(r"[\w'-]+", flags=re.UNICODE)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
PARAGRAPH_SPLIT = re.compile(r"\n\s*\n+")
CONFLICT_MARKER = re.compile(r"^(<<<<<<<|=======|>>>>>>>|\|\|\|\|\|\|\|)", flags=re.MULTILINE)

ATOM_LEVELS = ["glyph-seed", "syllable", "word", "sentence", "paragraph"]

VOWELS = set("aeiouyAEIOUY")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


def has_conflict_markers(text: str) -> bool:
    return bool(CONFLICT_MARKER.search(text))


def syllabify(word: str) -> list[str]:
    """Deterministic heuristic syllable splitting using consonant-vowel patterns.

    Splits at consonant boundaries between vowel groups. For example:
    "hello" → ["hel", "lo"], "beautiful" → ["beau", "ti", "ful"]
    """
    if len(word) <= 2:
        return [word] if word else []

    syllables: list[str] = []
    current = ""

    i = 0
    while i < len(word):
        ch = word[i]
        current += ch

        if ch.lower() in VOWELS:
            # Consume consecutive vowels into this syllable
            while i + 1 < len(word) and word[i + 1].lower() in VOWELS:
                i += 1
                current += word[i]

            # Look ahead for consonant cluster followed by vowel
            if i + 1 < len(word):
                # Count consonants ahead
                cons_start = i + 1
                cons_end = cons_start
                while cons_end < len(word) and word[cons_end].lower() not in VOWELS:
                    cons_end += 1

                num_cons = cons_end - cons_start
                if cons_end < len(word) and num_cons > 0:
                    # There's a vowel after the consonants — split
                    # Keep last consonant(s) for next syllable if multiple
                    if num_cons >= 2:
                        # Add all but last consonant to current
                        current += word[cons_start:cons_end - 1]
                        i = cons_end - 2
                    syllables.append(current)
                    current = ""
                # else: remaining chars are all consonants — they'll be added to current

        i += 1

    if current:
        if syllables and len(current) == 1 and current.lower() not in VOWELS:
            syllables[-1] += current
        else:
            syllables.append(current)

    return syllables if syllables else [word]


def atomize_glyphs_rich(text: str) -> list[GlyphSeed]:
    """Produce enriched glyph-seed objects with full metadata."""
    glyphs: list[GlyphSeed] = []
    pos = 0
    for ch in text:
        if ch.isspace():
            continue
        try:
            uname = unicodedata.name(ch, f"U+{ord(ch):04X}")
        except ValueError:
            uname = f"U+{ord(ch):04X}"

        glyphs.append(
            GlyphSeed(
                character=ch,
                unicode_name=uname,
                phoneme_hint=get_phoneme_hint(ch),
                historic_forms=get_historic_forms(ch),
                visual_mutations=get_visual_mutations(ch),
                thematic_tags=get_thematic_tags(ch),
                future_seeds=get_future_seeds(ch),
                position=pos,
            )
        )
        pos += 1
    return glyphs


def atomize_text(text: str) -> dict[str, list[str]]:
    """Fast-path atomization returning plain string lists for all 5 levels."""
    glyphs = [c for c in text if not c.isspace()]
    words = WORD_PATTERN.findall(text)
    syllables: list[str] = []
    for w in words:
        syllables.extend(syllabify(w))
    sentences = [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]
    paragraphs = [p.strip() for p in PARAGRAPH_SPLIT.split(text) if p.strip()]
    return {
        "glyph-seed": glyphs,
        "syllable": syllables,
        "word": words,
        "sentence": sentences,
        "paragraph": paragraphs,
    }


def atomize_text_rich(text: str) -> dict[str, Any]:
    """Full 5-level atomization with rich GlyphSeed objects at level 0."""
    glyphs = atomize_glyphs_rich(text)
    words = WORD_PATTERN.findall(text)
    syllables: list[str] = []
    for w in words:
        syllables.extend(syllabify(w))
    sentences = [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]
    paragraphs = [p.strip() for p in PARAGRAPH_SPLIT.split(text) if p.strip()]
    return {
        "glyph-seed": glyphs,
        "syllable": syllables,
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
