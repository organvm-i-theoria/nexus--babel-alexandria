from __future__ import annotations

import hashlib
import json
import shutil
import wave
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from nexus_babel.config import Settings
from nexus_babel.models import Atom, Document, IngestJob
from nexus_babel.services.canonicalization import apply_canonicalization, collect_current_corpus_paths
from nexus_babel.services.hypergraph import HypergraphProjector
from nexus_babel.services.text_utils import atomize_text, has_conflict_markers, sha256_file

TEXT_EXT = {".md", ".txt", ".yaml", ".yml"}
PDF_EXT = {".pdf"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
AUDIO_EXT = {".wav", ".mp3", ".flac"}


class IngestionService:
    def __init__(self, settings: Settings, hypergraph: HypergraphProjector):
        self.settings = settings
        self.hypergraph = hypergraph

    def ingest_batch(
        self,
        session: Session,
        source_paths: list[str],
        modalities: list[str],
        parse_options: dict[str, Any],
    ) -> dict[str, Any]:
        selected_paths = [self._resolve_path(p) for p in source_paths] if source_paths else collect_current_corpus_paths(self.settings.corpus_root)
        modality_filter = {m.lower() for m in modalities} if modalities else set()
        atom_levels = parse_options.get("atom_levels", ["glyph-seed", "word", "sentence", "paragraph"])
        atomize_enabled = bool(parse_options.get("atomize", True))

        job = IngestJob(status="running", request_payload={"source_paths": [str(p) for p in selected_paths], "modalities": modalities, "parse_options": parse_options})
        session.add(job)
        session.flush()

        files: list[dict[str, Any]] = []
        documents_ingested = 0
        atoms_created = 0
        checksums: list[str] = []
        errors: list[str] = []
        touched_docs: list[Document] = []

        for path in selected_paths:
            try:
                if not path.exists() or not path.is_file():
                    files.append({"path": str(path), "status": "error", "error": "File not found", "document_id": None})
                    errors.append(f"File not found: {path}")
                    continue

                modality = self._detect_modality(path)
                if modality_filter and modality not in modality_filter:
                    files.append({"path": str(path), "status": "skipped", "error": None, "document_id": None})
                    continue

                checksum = sha256_file(path)
                checksums.append(checksum)
                raw_storage_path = self._store_raw_payload(path, checksum)

                extracted_text = ""
                segments: dict[str, Any] = {}
                conflict = False

                if path.suffix.lower() in TEXT_EXT:
                    extracted_text = path.read_text(encoding="utf-8", errors="ignore")
                    conflict = has_conflict_markers(extracted_text)
                    segments = {
                        "line_count": extracted_text.count("\n") + 1,
                        "char_count": len(extracted_text),
                    }
                elif path.suffix.lower() in PDF_EXT:
                    extracted_text = self._extract_pdf_text(path)
                    segments = {
                        "char_count": len(extracted_text),
                        "page_count": self._pdf_page_count(path),
                    }
                elif path.suffix.lower() in IMAGE_EXT:
                    segments = self._extract_image_metadata(path)
                elif path.suffix.lower() in AUDIO_EXT:
                    segments = self._extract_audio_metadata(path)

                doc = self._upsert_document(
                    session=session,
                    path=path,
                    modality=modality,
                    checksum=checksum,
                    conflict=conflict,
                    extracted_text=extracted_text,
                    raw_storage_path=raw_storage_path,
                    segments=segments,
                )
                touched_docs.append(doc)

                if conflict:
                    files.append({"path": str(path), "status": "conflict", "document_id": doc.id, "error": "Conflict markers detected"})
                    continue

                atom_payloads: list[dict[str, Any]] = []
                if atomize_enabled and extracted_text:
                    atom_payloads = self._create_atoms(session, doc, extracted_text, atom_levels)
                    atoms_created += len(atom_payloads)

                hypergraph_ids = self.hypergraph.project_document(
                    document_id=doc.id,
                    document_payload={"path": doc.path, "modality": doc.modality, "checksum": doc.checksum},
                    atoms=atom_payloads[:500],
                )
                doc.provenance = {
                    **(doc.provenance or {}),
                    "raw_storage_path": str(raw_storage_path),
                    "segments": segments,
                    "hypergraph": hypergraph_ids,
                }
                doc.ingested = True
                doc.ingest_status = "ingested"

                documents_ingested += 1
                files.append({"path": str(path), "status": "ingested", "document_id": doc.id, "error": None})
            except Exception as exc:  # pragma: no cover - defensive
                errors.append(str(exc))
                files.append({"path": str(path), "status": "error", "document_id": None, "error": str(exc)})

        apply_canonicalization(session, touched_docs)

        digest = hashlib.sha256("\n".join(sorted(checksums)).encode("utf-8")).hexdigest() if checksums else ""
        summary = {
            "files": files,
            "documents_ingested": documents_ingested,
            "atoms_created": atoms_created,
            "provenance_digest": digest,
        }
        job.status = "completed" if not errors else "completed_with_errors"
        job.result_summary = summary
        job.errors = errors

        return {"job": job, **summary, "errors": errors}

    def get_job_status(self, session: Session, job_id: str) -> dict[str, Any]:
        job = session.scalar(select(IngestJob).where(IngestJob.id == job_id))
        if not job:
            raise ValueError(f"Ingest job {job_id} not found")

        summary = job.result_summary or {}
        return {
            "ingest_job_id": job.id,
            "status": job.status,
            "files": summary.get("files", []),
            "errors": job.errors or [],
            "documents_ingested": summary.get("documents_ingested", 0),
            "atoms_created": summary.get("atoms_created", 0),
            "provenance_digest": summary.get("provenance_digest", ""),
        }

    def _resolve_path(self, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return (self.settings.corpus_root / p).resolve()

    def _detect_modality(self, path: Path) -> str:
        ext = path.suffix.lower()
        if ext in TEXT_EXT:
            return "text"
        if ext in PDF_EXT:
            return "pdf"
        if ext in IMAGE_EXT:
            return "image"
        if ext in AUDIO_EXT:
            return "audio"
        return "binary"

    def _extract_pdf_text(self, path: Path) -> str:
        reader = PdfReader(str(path))
        chunks = []
        for page in reader.pages:
            chunks.append(page.extract_text() or "")
        return "\n".join(chunks)

    def _pdf_page_count(self, path: Path) -> int:
        reader = PdfReader(str(path))
        return len(reader.pages)

    def _extract_image_metadata(self, path: Path) -> dict[str, Any]:
        metadata = {"filename": path.name, "size_bytes": path.stat().st_size}
        try:
            from PIL import Image  # type: ignore

            with Image.open(path) as img:
                metadata.update({"width": img.width, "height": img.height, "mode": img.mode})
        except Exception:
            metadata.update({"width": None, "height": None})
        return metadata

    def _extract_audio_metadata(self, path: Path) -> dict[str, Any]:
        metadata = {"filename": path.name, "size_bytes": path.stat().st_size}
        if path.suffix.lower() == ".wav":
            with wave.open(str(path), "rb") as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                duration = frames / float(rate) if rate else 0.0
                metadata.update({"sample_rate": rate, "channels": wav.getnchannels(), "duration_seconds": duration})
        return metadata

    def _upsert_document(
        self,
        session: Session,
        path: Path,
        modality: str,
        checksum: str,
        conflict: bool,
        extracted_text: str,
        raw_storage_path: Path,
        segments: dict[str, Any],
    ) -> Document:
        resolved = str(path.resolve())
        doc = session.scalar(select(Document).where(Document.path == resolved))
        if not doc:
            doc = Document(
                path=resolved,
                title=path.name,
                modality=modality,
                checksum=checksum,
                size_bytes=path.stat().st_size,
                conflict_flag=conflict,
                ingest_status="conflict" if conflict else "parsed",
                ingested=not conflict,
                provenance={},
            )
            session.add(doc)
            session.flush()
        else:
            doc.title = path.name
            doc.modality = modality
            doc.checksum = checksum
            doc.size_bytes = path.stat().st_size
            doc.conflict_flag = conflict
            doc.ingest_status = "conflict" if conflict else "parsed"
            doc.ingested = not conflict

        doc.provenance = {
            **(doc.provenance or {}),
            "extracted_text": extracted_text,
            "segments": segments,
            "checksum": checksum,
            "raw_storage_path": str(raw_storage_path),
            "conflict": conflict,
        }
        return doc

    def _create_atoms(self, session: Session, doc: Document, text: str, atom_levels: list[str]) -> list[dict[str, Any]]:
        session.execute(delete(Atom).where(Atom.document_id == doc.id))
        atoms_map = atomize_text(text)
        payloads: list[dict[str, Any]] = []
        for level in atom_levels:
            values = atoms_map.get(level, [])
            for idx, content in enumerate(values, start=1):
                atom = Atom(
                    document_id=doc.id,
                    atom_level=level,
                    ordinal=idx,
                    content=content,
                    atom_metadata={"length": len(content)},
                )
                session.add(atom)
                session.flush()
                payloads.append(
                    {
                        "id": atom.id,
                        "document_id": doc.id,
                        "atom_level": level,
                        "ordinal": idx,
                        "content": content,
                    }
                )
        return payloads

    def _store_raw_payload(self, source_path: Path, checksum: str) -> Path:
        ext = source_path.suffix
        bucket = self.settings.object_storage_root
        bucket.mkdir(parents=True, exist_ok=True)
        destination = bucket / f"{checksum}{ext}"
        if not destination.exists():
            shutil.copy2(source_path, destination)
        return destination
