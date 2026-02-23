"""Seed text registry and Project Gutenberg provisioning."""

from __future__ import annotations

import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SeedText:
    title: str
    author: str
    language: str
    source_url: str
    local_path: Path | None = None
    atomization_status: str = "not_provisioned"


SEED_REGISTRY: list[dict[str, Any]] = [
    {
        "title": "The Odyssey",
        "author": "Homer",
        "language": "English",
        "source_url": "https://www.gutenberg.org/cache/epub/1727/pg1727.txt",
    },
    {
        "title": "The Divine Comedy",
        "author": "Dante Alighieri",
        "language": "English",
        "source_url": "https://www.gutenberg.org/cache/epub/8800/pg8800.txt",
    },
    {
        "title": "Leaves of Grass",
        "author": "Walt Whitman",
        "language": "English",
        "source_url": "https://www.gutenberg.org/cache/epub/1322/pg1322.txt",
    },
    {
        "title": "Ulysses",
        "author": "James Joyce",
        "language": "English",
        "source_url": "https://www.gutenberg.org/cache/epub/4300/pg4300.txt",
    },
    {
        "title": "Frankenstein",
        "author": "Mary Shelley",
        "language": "English",
        "source_url": "https://www.gutenberg.org/cache/epub/84/pg84.txt",
    },
]


class SeedCorpusService:
    def __init__(self, seeds_dir: Path):
        self.seeds_dir = seeds_dir
        self.seeds_dir.mkdir(parents=True, exist_ok=True)

    def list_seed_texts(self) -> list[dict[str, Any]]:
        result = []
        for entry in SEED_REGISTRY:
            local_path = self._local_path_for(entry["title"])
            exists = local_path.exists()
            result.append(
                {
                    "title": entry["title"],
                    "author": entry["author"],
                    "language": entry["language"],
                    "source_url": entry["source_url"],
                    "local_path": str(local_path) if exists else None,
                    "atomization_status": "provisioned" if exists else "not_provisioned",
                }
            )
        return result

    def provision_seed_text(self, title: str) -> dict[str, Any]:
        entry = self._find_entry(title)
        if not entry:
            raise ValueError(f"Unknown seed text: {title}")

        local_path = self._local_path_for(entry["title"])
        if local_path.exists():
            return {
                "title": entry["title"],
                "status": "already_provisioned",
                "local_path": str(local_path),
            }

        self._download(entry["source_url"], local_path)
        return {
            "title": entry["title"],
            "status": "provisioned",
            "local_path": str(local_path),
        }

    def _find_entry(self, title: str) -> dict[str, Any] | None:
        title_lower = title.lower()
        for entry in SEED_REGISTRY:
            if entry["title"].lower() == title_lower:
                return entry
        return None

    def _local_path_for(self, title: str) -> Path:
        safe_name = title.lower().replace(" ", "_").replace("'", "")
        return self.seeds_dir / f"{safe_name}.txt"

    def _download(self, url: str, dest: Path) -> None:
        urllib.request.urlretrieve(url, str(dest))  # noqa: S310
