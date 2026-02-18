from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


Mode = Literal["RAW", "PUBLIC"]


class IngestBatchRequest(BaseModel):
    source_paths: list[str] = Field(default_factory=list)
    modalities: list[str] = Field(default_factory=list)
    parse_options: dict[str, Any] = Field(default_factory=dict)


class IngestBatchResponse(BaseModel):
    ingest_job_id: str
    documents_ingested: int
    atoms_created: int
    provenance_digest: str


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
    atoms_created: int
    provenance_digest: str


class AnalyzeRequest(BaseModel):
    document_id: str | None = None
    branch_id: str | None = None
    layers: list[str] = Field(default_factory=list)
    mode: Mode = "PUBLIC"


class AnalyzeResponse(BaseModel):
    analysis_run_id: str
    mode: Mode
    layers: dict[str, Any]
    confidence_bundle: dict[str, float]
    hypergraph_ids: dict[str, Any]


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
