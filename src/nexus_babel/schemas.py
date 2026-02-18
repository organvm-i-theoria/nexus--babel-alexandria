from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


Mode = Literal["RAW", "PUBLIC"]
ExecutionMode = Literal["sync", "async", "shadow"]


class IngestBatchRequest(BaseModel):
    source_paths: list[str] = Field(default_factory=list)
    modalities: list[str] = Field(default_factory=list)
    parse_options: dict[str, Any] = Field(default_factory=dict)


class IngestBatchResponse(BaseModel):
    ingest_job_id: str
    documents_ingested: int
    documents_unchanged: int = 0
    atoms_created: int
    provenance_digest: str
    ingest_scope: str = "partial"
    warnings: list[str] = Field(default_factory=list)


class IngestFileStatus(BaseModel):
    path: str
    status: str
    document_id: str | None = None
    error: str | None = None


class IngestJobResponse(BaseModel):
    ingest_job_id: str
    status: str
    files: list[IngestFileStatus]
    errors: list[str]
    documents_ingested: int
    documents_unchanged: int = 0
    atoms_created: int
    provenance_digest: str
    ingest_scope: str = "partial"
    warnings: list[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    document_id: str | None = None
    branch_id: str | None = None
    layers: list[str] = Field(default_factory=list)
    mode: Mode = "PUBLIC"
    execution_mode: ExecutionMode = "sync"
    plugin_profile: str | None = None


class AnalyzeResponse(BaseModel):
    analysis_run_id: str | None = None
    mode: Mode
    layers: dict[str, Any]
    confidence_bundle: dict[str, float]
    hypergraph_ids: dict[str, Any]
    plugin_provenance: dict[str, Any] = Field(default_factory=dict)
    job_id: str | None = None
    status: str = "completed"


class EvolveBranchRequest(BaseModel):
    parent_branch_id: str | None = None
    root_document_id: str | None = None
    event_type: str
    event_payload: dict[str, Any] = Field(default_factory=dict)
    mode: Mode = "PUBLIC"


class EvolveBranchResponse(BaseModel):
    new_branch_id: str
    event_id: str
    diff_summary: dict[str, Any]


class BranchEventView(BaseModel):
    branch_id: str
    event_id: str
    event_index: int
    event_type: str
    event_payload: dict[str, Any]
    diff_summary: dict[str, Any]
    created_at: datetime


class BranchTimelineResponse(BaseModel):
    branch_id: str
    root_document_id: str | None
    events: list[BranchEventView]
    replay_snapshot: dict[str, Any]


class RhetoricalAnalysisRequest(BaseModel):
    text: str | None = None
    document_id: str | None = None
    audience_profile: dict[str, Any] = Field(default_factory=dict)


class RhetoricalAnalysisResponse(BaseModel):
    ethos_score: float
    pathos_score: float
    logos_score: float
    strategies: list[str]
    fallacies: list[str]
    explainability: dict[str, Any]


class GovernanceEvaluateRequest(BaseModel):
    candidate_output: str
    mode: Mode = "PUBLIC"


class GovernanceEvaluateResponse(BaseModel):
    allow: bool
    policy_hits: list[str]
    redactions: list[str]
    audit_id: str
    decision_trace: dict[str, Any] = Field(default_factory=dict)


class JobSubmitRequest(BaseModel):
    job_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    execution_mode: ExecutionMode = "async"
    idempotency_key: str | None = None
    max_attempts: int = Field(default=3, ge=1, le=10)


class JobSubmitResponse(BaseModel):
    job_id: str
    status: str
    job_type: str
    execution_mode: ExecutionMode


class JobAttemptView(BaseModel):
    attempt_number: int
    status: str
    error_text: str | None = None
    runtime_ms: int | None = None
    started_at: datetime
    finished_at: datetime | None = None


class JobArtifactView(BaseModel):
    artifact_type: str
    artifact_ref: str | None = None
    artifact_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class JobStatusResponse(BaseModel):
    job_id: str
    job_type: str
    status: str
    payload: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    error_text: str | None = None
    execution_mode: ExecutionMode
    idempotency_key: str | None = None
    max_attempts: int
    attempt_count: int
    next_run_at: datetime
    lease_owner: str | None = None
    lease_expires_at: datetime | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime
    attempts: list[JobAttemptView] = Field(default_factory=list)
    artifacts: list[JobArtifactView] = Field(default_factory=list)


class AnalysisRunResponse(BaseModel):
    analysis_run_id: str
    document_id: str | None = None
    branch_id: str | None = None
    mode: Mode
    execution_mode: ExecutionMode
    plugin_profile: str | None = None
    layers: list[str] = Field(default_factory=list)
    confidence_bundle: dict[str, float] = Field(default_factory=dict)
    results: dict[str, Any] = Field(default_factory=dict)
    run_metadata: dict[str, Any] = Field(default_factory=dict)
    layer_outputs: list[dict[str, Any]] = Field(default_factory=list)


class BranchReplayResponse(BaseModel):
    branch_id: str
    event_count: int
    text_hash: str
    preview: str
    replay_snapshot: dict[str, Any] = Field(default_factory=dict)


class BranchCompareResponse(BaseModel):
    left_branch_id: str
    right_branch_id: str
    left_hash: str
    right_hash: str
    distance: int
    same: bool
    preview_left: str
    preview_right: str
