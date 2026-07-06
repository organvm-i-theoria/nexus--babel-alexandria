from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_babel.config import Settings
from nexus_babel.db import DBManager
from nexus_babel.models import AnalysisRun, Base, Document, Job, JobArtifact, JobAttempt, utcnow
from nexus_babel.services.jobs import JobService


class RecordingIngestionService:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def ingest_batch(
        self,
        *,
        session: Session,
        source_paths: list[str],
        modalities: list[str],
        parse_options: dict,
    ) -> dict:
        self.calls.append(
            {
                "session": session,
                "source_paths": source_paths,
                "modalities": modalities,
                "parse_options": parse_options,
            }
        )
        return {
            "job": SimpleNamespace(id="ingest-job-1"),
            "documents_ingested": 2,
            "atoms_created": 5,
            "provenance_digest": "digest-123",
            "warnings": ["skipped duplicate"],
        }


class RecordingAnalysisService:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def analyze(
        self,
        *,
        session: Session,
        document_id: str | None,
        branch_id: str | None,
        layers: list[str],
        mode: str,
        execution_mode: str,
        plugin_profile: str | None,
        job_id: str | None,
    ) -> tuple[AnalysisRun, dict]:
        self.calls.append(
            {
                "document_id": document_id,
                "branch_id": branch_id,
                "layers": layers,
                "mode": mode,
                "execution_mode": execution_mode,
                "plugin_profile": plugin_profile,
                "job_id": job_id,
            }
        )
        run = AnalysisRun(
            document_id=document_id,
            branch_id=branch_id,
            mode=mode.upper(),
            execution_mode=execution_mode,
            plugin_profile=plugin_profile,
            job_id=job_id,
            layers=layers,
            confidence={"token": 0.91},
            results={"token": {"token_count": 3}},
            run_metadata={},
        )
        session.add(run)
        session.flush()
        return run, {
            "mode": mode.upper(),
            "layers": {
                "token": {"token_count": 3},
                "syntax": {"sentence_count": 1},
            },
            "confidence_bundle": {"token": 0.91, "syntax": 0.88},
            "hypergraph_ids": {"document_id": document_id},
            "plugin_provenance": {"token": {"provider_name": "fake"}},
        }


class RecordingEvolutionService:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def replay_branch(self, *, session: Session, branch_id: str) -> dict:
        self.calls.append({"session": session, "branch_id": branch_id})
        return {"branch_id": branch_id, "text_hash": "hash-abc", "event_count": 4}


class RecordingHypergraph:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def integrity_for_document(self, document: Document) -> dict:
        self.calls.append(document.id)
        if document.title == "inconsistent":
            return {"consistent": False, "missing_nodes": ["atom-9"]}
        return {"consistent": True, "missing_nodes": []}


@dataclass
class JobHarness:
    service: JobService
    ingestion: RecordingIngestionService
    analysis: RecordingAnalysisService
    evolution: RecordingEvolutionService
    hypergraph: RecordingHypergraph


@pytest.fixture
def job_session(tmp_path):
    db = DBManager(f"sqlite:///{tmp_path / 'jobs.db'}")
    db.create_all(Base.metadata)
    session = db.session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def job_harness(tmp_path) -> JobHarness:
    settings = Settings(
        environment="test",
        database_url=f"sqlite:///{tmp_path / 'jobs.db'}",
        corpus_root=tmp_path,
        object_storage_root=tmp_path / "objects",
        worker_lease_seconds=11,
    )
    ingestion = RecordingIngestionService()
    analysis = RecordingAnalysisService()
    evolution = RecordingEvolutionService()
    hypergraph = RecordingHypergraph()
    return JobHarness(
        service=JobService(
            settings=settings,
            ingestion_service=ingestion,
            analysis_service=analysis,
            evolution_service=evolution,
            hypergraph=hypergraph,
        ),
        ingestion=ingestion,
        analysis=analysis,
        evolution=evolution,
        hypergraph=hypergraph,
    )


def test_process_ingest_batch_records_attempt_result_and_artifact(job_session, job_harness):
    service = job_harness.service
    job = service.submit(
        job_session,
        job_type="ingest_batch",
        payload={
            "source_paths": ["a.md", "b.pdf"],
            "modalities": ["text", "pdf"],
            "parse_options": {"atomize": True},
        },
        idempotency_key="batch-1",
        created_by="operator",
    )
    duplicate = service.submit(
        job_session,
        job_type="ingest_batch",
        payload={"source_paths": ["ignored.md"]},
        idempotency_key="batch-1",
    )

    processed = service.process_next(job_session, "worker-a")
    job_session.flush()

    assert duplicate.id == job.id
    assert processed is job
    assert job.status == "succeeded"
    assert job.lease_owner is None
    assert job.result == {
        "ingest_job_id": "ingest-job-1",
        "documents_ingested": 2,
        "atoms_created": 5,
        "provenance_digest": "digest-123",
        "warnings": ["skipped duplicate"],
    }
    assert job_harness.ingestion.calls == [
        {
            "session": job_session,
            "source_paths": ["a.md", "b.pdf"],
            "modalities": ["text", "pdf"],
            "parse_options": {"atomize": True},
        }
    ]

    status = service.get_job(job_session, job.id)
    assert status["attempts"][0]["attempt_number"] == 1
    assert status["attempts"][0]["status"] == "succeeded"
    assert status["artifacts"][0]["artifact_type"] == "ingest_batch_result"
    assert status["artifacts"][0]["artifact_payload"] == {
        "ingest_job_id": "ingest-job-1",
        "documents_ingested": 2,
    }


def test_analyze_job_records_analysis_run_and_artifact(job_session, job_harness):
    service = job_harness.service
    job = service.submit(
        job_session,
        job_type="analyze",
        payload={
            "document_id": "doc-1",
            "branch_id": None,
            "layers": ["token", "syntax"],
            "mode": "raw",
            "plugin_profile": "deterministic",
        },
    )

    service.execute(job_session, job)
    job_session.flush()

    assert job.status == "succeeded"
    assert job_harness.analysis.calls == [
        {
            "document_id": "doc-1",
            "branch_id": None,
            "layers": ["token", "syntax"],
            "mode": "raw",
            "execution_mode": "async",
            "plugin_profile": "deterministic",
            "job_id": job.id,
        }
    ]
    last_run = service.last_analysis_run_for_job(job_session, job.id)
    assert last_run is not None
    assert last_run.id == job.result["analysis_run_id"]

    artifact = job_session.scalar(select(JobArtifact).where(JobArtifact.job_id == job.id))
    assert artifact is not None
    assert artifact.artifact_type == "analyze_result"
    assert artifact.artifact_payload == {
        "analysis_run_id": last_run.id,
        "layer_count": 2,
    }


def test_branch_replay_job_dispatches_and_stores_replay_artifact(job_session, job_harness):
    service = job_harness.service
    job = service.submit(
        job_session,
        job_type="branch_replay",
        payload={"branch_id": "branch-7"},
    )

    service.execute(job_session, job)
    job_session.flush()

    assert job.status == "succeeded"
    assert job.result == {"branch_id": "branch-7", "text_hash": "hash-abc", "event_count": 4}
    assert job_harness.evolution.calls == [{"session": job_session, "branch_id": "branch-7"}]

    artifact = job_session.scalar(select(JobArtifact).where(JobArtifact.job_id == job.id))
    assert artifact is not None
    assert artifact.artifact_type == "branch_replay_result"
    assert artifact.artifact_payload == {
        "branch_id": "branch-7",
        "text_hash": "hash-abc",
    }


def test_integrity_audit_checks_only_ingested_documents_and_reports_findings(job_session, job_harness):
    consistent = Document(
        path="consistent.md",
        title="consistent",
        modality="text",
        checksum="sha1",
        size_bytes=11,
        ingested=True,
        provenance={},
        modality_status={},
        provider_summary={},
    )
    inconsistent = Document(
        path="inconsistent.md",
        title="inconsistent",
        modality="text",
        checksum="sha2",
        size_bytes=12,
        ingested=True,
        provenance={},
        modality_status={},
        provider_summary={},
    )
    skipped = Document(
        path="pending.md",
        title="pending",
        modality="text",
        checksum="sha3",
        size_bytes=13,
        ingested=False,
        provenance={},
        modality_status={},
        provider_summary={},
    )
    job_session.add_all([consistent, inconsistent, skipped])
    job_session.flush()
    job = job_harness.service.submit(job_session, job_type="integrity_audit", payload={})

    job_harness.service.execute(job_session, job)
    job_session.flush()

    assert job.status == "succeeded"
    assert job.result == {
        "document_count": 2,
        "inconsistencies": [
            {
                "document_id": inconsistent.id,
                "integrity": {"consistent": False, "missing_nodes": ["atom-9"]},
            }
        ],
    }
    assert set(job_harness.hypergraph.calls) == {consistent.id, inconsistent.id}


def test_execute_records_retry_then_terminal_failure_for_unsupported_job(job_session, job_harness):
    service = job_harness.service
    job = service.submit(job_session, job_type="not_supported", payload={}, max_attempts=2)

    service.execute(job_session, job)
    job_session.flush()

    assert job.status == "retry_wait"
    assert job.attempt_count == 1
    assert "Unsupported job_type: not_supported" in job.error_text
    first_attempt = job_session.scalar(select(JobAttempt).where(JobAttempt.job_id == job.id))
    assert first_attempt is not None
    assert first_attempt.status == "failed"
    assert first_attempt.finished_at is not None
    assert first_attempt.runtime_ms is not None

    service.execute(job_session, job)
    job_session.flush()

    attempts = job_session.scalars(
        select(JobAttempt).where(JobAttempt.job_id == job.id).order_by(JobAttempt.attempt_number)
    ).all()
    assert job.status == "failed"
    assert job.lease_owner is None
    assert job.lease_expires_at is None
    assert [attempt.attempt_number for attempt in attempts] == [1, 2]
    assert [attempt.status for attempt in attempts] == ["failed", "failed"]


def test_complete_stale_leases_requeues_retryable_jobs_and_fails_exhausted_jobs(job_session, job_harness):
    now = utcnow()
    retryable = Job(
        job_type="analyze",
        status="running",
        payload={},
        max_attempts=3,
        attempt_count=1,
        next_run_at=now - timedelta(minutes=2),
        lease_owner="old-worker",
        lease_expires_at=now - timedelta(seconds=1),
    )
    exhausted = Job(
        job_type="analyze",
        status="running",
        payload={},
        max_attempts=2,
        attempt_count=2,
        next_run_at=now - timedelta(minutes=2),
        lease_owner="old-worker",
        lease_expires_at=now - timedelta(seconds=1),
    )
    still_leased = Job(
        job_type="analyze",
        status="running",
        payload={},
        max_attempts=3,
        attempt_count=1,
        next_run_at=now - timedelta(minutes=2),
        lease_owner="old-worker",
        lease_expires_at=now + timedelta(minutes=1),
    )
    job_session.add_all([retryable, exhausted, still_leased])
    job_session.flush()

    completed = job_harness.service.complete_stale_leases(job_session, "janitor")

    assert completed == 2
    assert retryable.status == "retry_wait"
    assert retryable.lease_owner == "janitor"
    assert retryable.lease_expires_at is None
    assert retryable.next_run_at > now
    assert exhausted.status == "failed"
    assert exhausted.lease_owner == "janitor"
    assert exhausted.lease_expires_at is None
    assert still_leased.status == "running"
    assert still_leased.lease_owner == "old-worker"
