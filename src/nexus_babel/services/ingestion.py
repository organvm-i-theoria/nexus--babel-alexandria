from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from nexus_babel.config import Settings
from nexus_babel.models import Atom, Document, IngestJob, ProjectionLedger
from nexus_babel.services.canonicalization import apply_canonicalization, collect_current_corpus_paths
from nexus_babel.services.hypergraph import HypergraphProjector
from nexus_babel.services.ingestion_media import (
    AUDIO_EXT,
    IMAGE_EXT,
    PDF_EXT,
    TEXT_EXT,
    derive_modality_status,
    derive_text_segments,
    detect_modality,
    extract_audio_metadata,
    extract_image_metadata,
    extract_pdf_text,
    pdf_page_count,
)
from nexus_babel.services import ingestion_projection
from nexus_babel.services.text_utils import (
    ATOM_FILENAME_SCHEMA_VERSION,
    atomize_text_rich,
    deterministic_atom_filename,
    has_conflict_markers,
    normalize_atom_token,
    resolve_atomization_selection,
    sha256_file,
)


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
        ingest_scope = "partial" if source_paths else "full"
        selected_paths = [self._resolve_path(p) for p in source_paths] if source_paths else collect_current_corpus_paths(self.settings.corpus_root)
        modality_filter = {m.lower() for m in modalities} if modalities else set()
        atom_tracks, atom_levels = resolve_atomization_selection(
            atom_tracks=parse_options.get("atom_tracks"),
            atom_levels=parse_options.get("atom_levels"),
        )
        atomize_enabled = bool(parse_options.get("atomize", True))
        force_reingest = bool(parse_options.get("force", False))
        normalized_parse_options = {
            **parse_options,
            "atom_tracks": atom_tracks,
            "atom_levels": atom_levels,
            "atomize": atomize_enabled,
            "force": force_reingest,
        }

        job = IngestJob(
            status="running",
            request_payload={
                "source_paths": [str(p) for p in selected_paths],
                "modalities": modalities,
                "parse_options": normalized_parse_options,
            },
        )
        session.add(job)
        session.flush()

        files: list[dict[str, Any]] = []
        documents_ingested = 0
        atoms_created = 0
        documents_unchanged = 0
        checksums: list[str] = []
        errors: list[str] = []
        warnings: list[str] = []
        updated_doc_ids: set[str] = set()

        for path in selected_paths:
            try:
                if not path.exists() or not path.is_file():
                    files.append({"path": str(path), "status": "error", "error": "File not found", "document_id": None})
                    errors.append(f"File not found: {path}")
                    continue

                modality = detect_modality(path)
                if modality_filter and modality not in modality_filter:
                    files.append({"path": str(path), "status": "skipped", "error": None, "document_id": None})
                    continue

                checksum = sha256_file(path)
                checksums.append(checksum)
                existing = session.scalar(select(Document).where(Document.path == str(path.resolve())))
                if existing and existing.checksum == checksum and existing.ingested and not force_reingest:
                    existing.ingest_status = "unchanged"
                    existing.modality_status = {
                        **(existing.modality_status or {}),
                        existing.modality: "complete",
                    }
                    files.append({"path": str(path), "status": "unchanged", "document_id": existing.id, "error": None})
                    documents_unchanged += 1
                    continue

                raw_storage_path = self._store_raw_payload(path, checksum)

                extracted_text = ""
                segments: dict[str, Any] = {}
                conflict = False
                conflict_reason: str | None = None

                if path.suffix.lower() in TEXT_EXT:
                    extracted_text = path.read_text(encoding="utf-8", errors="ignore")
                    conflict = has_conflict_markers(extracted_text)
                    if conflict:
                        conflict_reason = "Conflict markers detected"
                    segments = {
                        "line_count": extracted_text.count("\n") + 1,
                        "char_count": len(extracted_text),
                    }
                    segments.update(derive_text_segments(extracted_text, is_pdf=False))
                elif path.suffix.lower() in PDF_EXT:
                    extracted_text = extract_pdf_text(path)
                    segments = {
                        "char_count": len(extracted_text),
                        "page_count": pdf_page_count(path),
                    }
                    segments.update(derive_text_segments(extracted_text, is_pdf=True))
                elif path.suffix.lower() in IMAGE_EXT:
                    segments = extract_image_metadata(path)
                elif path.suffix.lower() in AUDIO_EXT:
                    segments = extract_audio_metadata(path)

                doc = self._upsert_document(
                    session=session,
                    path=path,
                    modality=modality,
                    checksum=checksum,
                    conflict=conflict,
                    conflict_reason=conflict_reason,
                    extracted_text=extracted_text,
                    raw_storage_path=raw_storage_path,
                    segments=segments,
                )

                if conflict:
                    doc.conflict_reason = conflict_reason
                    doc.modality_status = {doc.modality: "failed"}
                    files.append({"path": str(path), "status": "conflict", "document_id": doc.id, "error": conflict_reason})
                    continue

                atom_payloads: list[dict[str, Any]] = []
                if atomize_enabled and extracted_text:
                    atom_payloads = self._create_atoms(session, doc, extracted_text, atom_levels)
                    atoms_created += len(atom_payloads)
                doc.atom_count = len(atom_payloads)
                doc.graph_projected_atom_count = 0
                doc.graph_projection_status = "pending"

                projection_warning: str | None = None
                hypergraph_ids: dict[str, Any] = {}
                try:
                    hypergraph_ids = self.hypergraph.project_document(
                        document_id=doc.id,
                        document_payload={"path": doc.path, "modality": doc.modality, "checksum": doc.checksum},
                        atoms=atom_payloads,
                    )
                    doc.graph_projected_atom_count = len(atom_payloads)
                    doc.graph_projection_status = "complete" if doc.graph_projected_atom_count == doc.atom_count else "partial"
                    self._update_projection_ledger(session, doc.id, atom_payloads, status="projected")
                except Exception as graph_exc:  # pragma: no cover - fallback path
                    projection_warning = f"Graph projection failed: {graph_exc}"
                    doc.graph_projection_status = "failed"
                    self._update_projection_ledger(session, doc.id, atom_payloads, status="failed", error=projection_warning)
                    warnings.append(f"{path}: {projection_warning}")

                doc.provenance = {
                    **(doc.provenance or {}),
                    "raw_storage_path": str(raw_storage_path),
                    "segments": segments,
                    "hypergraph": hypergraph_ids,
                    "ingest_scope": ingest_scope,
                    "atomization": {
                        "atom_tracks": atom_tracks,
                        "active_atom_levels": atom_levels,
                        "filename_schema_version": ATOM_FILENAME_SCHEMA_VERSION,
                    },
                }
                doc.modality_status = {
                    **(doc.modality_status or {}),
                    doc.modality: derive_modality_status(doc.modality, projection_warning, segments),
                }
                doc.provider_summary = {
                    **(doc.provider_summary or {}),
                    "ingestion_provider": "builtin",
                    "projection_provider": "neo4j" if self.hypergraph.enabled else "local_cache",
                }
                doc.ingested = True
                doc.ingest_status = "ingested" if not projection_warning else "ingested_with_warnings"
                updated_doc_ids.add(doc.id)

                documents_ingested += 1
                files.append(
                    {
                        "path": str(path),
                        "status": doc.ingest_status,
                        "document_id": doc.id,
                        "error": projection_warning,
                    }
                )
            except Exception as exc:  # pragma: no cover - defensive
                errors.append(str(exc))
                files.append({"path": str(path), "status": "error", "document_id": None, "error": str(exc)})

        apply_canonicalization(session)
        self._apply_cross_modal_links(session, updated_doc_ids)

        digest = hashlib.sha256("\n".join(sorted(checksums)).encode("utf-8")).hexdigest() if checksums else ""
        summary = {
            "files": files,
            "documents_ingested": documents_ingested,
            "documents_unchanged": documents_unchanged,
            "atoms_created": atoms_created,
            "provenance_digest": digest,
            "ingest_scope": ingest_scope,
            "warnings": warnings,
        }
        job.status = "completed" if not errors else "completed_with_errors"
        job.result_summary = summary
        job.errors = errors

        return {"job": job, **summary, "errors": errors, "warnings": warnings}

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
            "documents_unchanged": summary.get("documents_unchanged", 0),
            "provenance_digest": summary.get("provenance_digest", ""),
            "ingest_scope": summary.get("ingest_scope", "partial"),
            "warnings": summary.get("warnings", []),
        }

    def _resolve_path(self, path: str) -> Path:
        root = self.settings.corpus_root.resolve()
        p = Path(path)
        candidate = p.resolve() if p.is_absolute() else (root / p).resolve()
        if not self._is_within_root(candidate, root):
            raise ValueError(f"Path escapes corpus_root and is not allowed: {path}")
        return candidate

    def _is_within_root(self, candidate: Path, root: Path) -> bool:
        try:
            candidate.relative_to(root)
            return True
        except ValueError:
            return False

    def _upsert_document(
        self,
        session: Session,
        path: Path,
        modality: str,
        checksum: str,
        conflict: bool,
        conflict_reason: str | None,
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
                conflict_reason=conflict_reason,
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
            doc.conflict_reason = conflict_reason
            doc.ingest_status = "conflict" if conflict else "parsed"
            doc.ingested = not conflict

        doc.provenance = {
            **(doc.provenance or {}),
            "extracted_text": extracted_text,
            "segments": segments,
            "checksum": checksum,
            "raw_storage_path": str(raw_storage_path),
            "conflict": conflict,
            "conflict_reason": conflict_reason,
        }
        return doc

    def _create_atoms(self, session: Session, doc: Document, text: str, atom_levels: list[str]) -> list[dict[str, Any]]:
        session.execute(delete(Atom).where(Atom.document_id == doc.id))
        session.execute(delete(ProjectionLedger).where(ProjectionLedger.document_id == doc.id))
        rich = atomize_text_rich(text)
        atoms_to_add: list[Atom] = []
        ledger_rows: list[ProjectionLedger] = []
        payloads: list[dict[str, Any]] = []
        filename_seen: dict[tuple[str, str], int] = {}
        for level in atom_levels:
            values = rich.get(level, [])
            for idx, item in enumerate(values, start=1):
                atom_id = str(uuid4())
                if level == "glyph-seed" and hasattr(item, "character"):
                    content = item.character
                    metadata_json = item.model_dump()
                else:
                    content = str(item)
                    metadata_json = None
                normalized_token = normalize_atom_token(content)
                dedupe_key = (level, normalized_token)
                duplicate_index = filename_seen.get(dedupe_key, 0) + 1
                filename_seen[dedupe_key] = duplicate_index
                filename = deterministic_atom_filename(
                    document_title=doc.title,
                    atom_level=level,
                    ordinal=idx,
                    content=content,
                    duplicate_index=duplicate_index,
                )
                atom = Atom(
                    id=atom_id,
                    document_id=doc.id,
                    atom_level=level,
                    ordinal=idx,
                    content=content,
                    atom_metadata={
                        "length": len(content),
                        "filename": filename,
                        "filename_schema_version": ATOM_FILENAME_SCHEMA_VERSION,
                        "normalized_token": normalized_token,
                        "duplicate_index": duplicate_index,
                    },
                    metadata_json=metadata_json,
                )
                atoms_to_add.append(atom)
                ledger_rows.append(
                    ProjectionLedger(
                        document_id=doc.id,
                        atom_id=atom_id,
                        status="pending",
                        attempt_count=0,
                    )
                )
                payloads.append(
                    {
                        "id": atom_id,
                        "document_id": doc.id,
                        "atom_level": level,
                        "ordinal": idx,
                        "content": content,
                        "filename": filename,
                    }
                )
        if atoms_to_add:
            session.add_all(atoms_to_add)
            session.add_all(ledger_rows)
            session.flush()
        return payloads

    def _store_raw_payload(self, source_path: Path, checksum: str) -> Path:
        ext = source_path.suffix
        bucket = self.settings.object_storage_root
        bucket.mkdir(parents=True, exist_ok=True)
        destination = bucket / f"{checksum}{ext}"
        if not destination.exists():
            shutil.copy2(source_path, destination)
        return destination

    def _update_projection_ledger(
        self,
        session: Session,
        document_id: str,
        atom_payloads: list[dict[str, Any]],
        *,
        status: str,
        error: str | None = None,
    ) -> None:
        ingestion_projection.update_projection_ledger(
            session,
            document_id=document_id,
            atom_payloads=atom_payloads,
            status=status,
            error=error,
        )

    def _apply_cross_modal_links(self, session: Session, updated_doc_ids: set[str]) -> None:
        ingestion_projection.apply_cross_modal_links(session, updated_doc_ids=updated_doc_ids)
