from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_babel.models import Document
from nexus_babel.services.auth import AuthContext
from nexus_babel.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    BranchEventView,
    BranchTimelineResponse,
    EvolveBranchRequest,
    EvolveBranchResponse,
    GovernanceEvaluateRequest,
    GovernanceEvaluateResponse,
    IngestBatchRequest,
    IngestBatchResponse,
    IngestFileStatus,
    IngestJobResponse,
    RhetoricalAnalysisRequest,
    RhetoricalAnalysisResponse,
)

router = APIRouter(prefix="/api/v1")


def _session(request: Request) -> Session:
    return request.app.state.db.session()


def _require_auth(min_role: str = "viewer") -> Callable:
    def dependency(
        request: Request,
        x_nexus_api_key: str | None = Header(default=None, alias="X-Nexus-API-Key"),
    ) -> AuthContext:
        session = request.app.state.db.session()
        try:
            ctx = request.app.state.auth_service.authenticate(session, x_nexus_api_key)
            if not ctx:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing or invalid API key",
                )
            if not request.app.state.auth_service.role_allows(ctx.role, min_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{ctx.role}' lacks required permission '{min_role}'",
                )
            request.state.auth_context = ctx
            session.commit()
            return ctx
        finally:
            session.close()

    return dependency


def _enforce_mode(request: Request, ctx: AuthContext, mode: str) -> None:
    if not request.app.state.auth_service.mode_allows(ctx.role, mode, request.app.state.settings.raw_mode_enabled):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{ctx.role}' is not allowed to execute mode '{mode.upper()}'",
        )


@router.post("/ingest/batch", response_model=IngestBatchResponse, dependencies=[Depends(_require_auth("operator"))])
def ingest_batch(payload: IngestBatchRequest, request: Request) -> IngestBatchResponse:
    session = _session(request)
    try:
        result = request.app.state.ingestion_service.ingest_batch(
            session=session,
            source_paths=payload.source_paths,
            modalities=payload.modalities,
            parse_options=payload.parse_options,
        )
        session.commit()
        return IngestBatchResponse(
            ingest_job_id=result["job"].id,
            documents_ingested=result["documents_ingested"],
            atoms_created=result["atoms_created"],
            provenance_digest=result["provenance_digest"],
            ingest_scope=result["ingest_scope"],
            warnings=result["warnings"],
        )
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        session.close()


@router.get("/ingest/jobs/{job_id}", response_model=IngestJobResponse, dependencies=[Depends(_require_auth("viewer"))])
def ingest_job(job_id: str, request: Request) -> IngestJobResponse:
    session = _session(request)
    try:
        result = request.app.state.ingestion_service.get_job_status(session, job_id)
        return IngestJobResponse(
            ingest_job_id=result["ingest_job_id"],
            status=result["status"],
            files=[IngestFileStatus(**item) for item in result["files"]],
            errors=result["errors"],
            documents_ingested=result["documents_ingested"],
            atoms_created=result["atoms_created"],
            provenance_digest=result["provenance_digest"],
            ingest_scope=result["ingest_scope"],
            warnings=result["warnings"],
        )
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        session.close()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    payload: AnalyzeRequest,
    request: Request,
    auth_context: AuthContext = Depends(_require_auth("operator")),
) -> AnalyzeResponse:
    session = _session(request)
    try:
        _enforce_mode(request, auth_context, payload.mode)
        if payload.document_id:
            doc = session.get(Document, payload.document_id)
            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")
            if doc.conflict_flag or not doc.ingested:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Document is conflicted or non-ingestable; analysis is blocked",
                )
        run, result = request.app.state.analysis_service.analyze(
            session=session,
            document_id=payload.document_id,
            branch_id=payload.branch_id,
            layers=payload.layers,
            mode=payload.mode,
        )
        session.commit()
        return AnalyzeResponse(
            analysis_run_id=run.id,
            mode=result["mode"],
            layers=result["layers"],
            confidence_bundle=result["confidence_bundle"],
            hypergraph_ids=result["hypergraph_ids"],
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        session.close()


@router.post("/evolve/branch", response_model=EvolveBranchResponse)
def evolve_branch(
    payload: EvolveBranchRequest,
    request: Request,
    auth_context: AuthContext = Depends(_require_auth("operator")),
) -> EvolveBranchResponse:
    session = _session(request)
    try:
        _enforce_mode(request, auth_context, payload.mode)
        branch, event = request.app.state.evolution_service.evolve_branch(
            session=session,
            parent_branch_id=payload.parent_branch_id,
            root_document_id=payload.root_document_id,
            event_type=payload.event_type,
            event_payload=payload.event_payload,
            mode=payload.mode,
        )
        session.commit()
        return EvolveBranchResponse(new_branch_id=branch.id, event_id=event.id, diff_summary=event.diff_summary)
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        session.close()


@router.get("/branches/{branch_id}/timeline", response_model=BranchTimelineResponse, dependencies=[Depends(_require_auth("viewer"))])
def branch_timeline(branch_id: str, request: Request) -> BranchTimelineResponse:
    session = _session(request)
    try:
        timeline = request.app.state.evolution_service.get_timeline(session=session, branch_id=branch_id)
        branch = timeline["branch"]
        events = [
            BranchEventView(
                branch_id=e.branch_id,
                event_id=e.id,
                event_index=e.event_index,
                event_type=e.event_type,
                event_payload=e.event_payload,
                diff_summary=e.diff_summary,
                created_at=e.created_at,
            )
            for e in timeline["events"]
        ]
        return BranchTimelineResponse(
            branch_id=branch.id,
            root_document_id=branch.root_document_id,
            events=events,
            replay_snapshot=timeline["replay_snapshot"],
        )
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        session.close()


@router.post("/rhetorical_analysis", response_model=RhetoricalAnalysisResponse)
def rhetorical_analysis(
    payload: RhetoricalAnalysisRequest,
    request: Request,
    auth_context: AuthContext = Depends(_require_auth("operator")),
) -> RhetoricalAnalysisResponse:
    session = _session(request)
    try:
        _enforce_mode(request, auth_context, "PUBLIC")
        text = payload.text
        if not text and payload.document_id:
            doc = session.get(Document, payload.document_id)
            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")
            text = str((doc.provenance or {}).get("extracted_text", ""))
        text = text or ""
        result = request.app.state.rhetorical_analyzer.analyze(text)
        return RhetoricalAnalysisResponse(**result)
    finally:
        session.close()


@router.post("/governance/evaluate", response_model=GovernanceEvaluateResponse)
def governance_evaluate(
    payload: GovernanceEvaluateRequest,
    request: Request,
    auth_context: AuthContext = Depends(_require_auth("operator")),
) -> GovernanceEvaluateResponse:
    session = _session(request)
    try:
        _enforce_mode(request, auth_context, payload.mode)
        decision = request.app.state.governance_service.evaluate(
            session=session,
            candidate_output=payload.candidate_output,
            mode=payload.mode,
        )
        session.commit()
        return GovernanceEvaluateResponse(
            allow=decision["allow"],
            policy_hits=decision["policy_hits"],
            redactions=decision["redactions"],
            audit_id=decision["audit_id"],
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        session.close()


@router.get("/hypergraph/documents/{document_id}/integrity", dependencies=[Depends(_require_auth("viewer"))])
def hypergraph_integrity(document_id: str, request: Request) -> dict:
    session = _session(request)
    try:
        doc = session.get(Document, document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return request.app.state.hypergraph.integrity_for_document(doc)
    finally:
        session.close()


@router.get("/documents", dependencies=[Depends(_require_auth("viewer"))])
def list_documents(request: Request) -> dict:
    session = _session(request)
    try:
        docs = session.scalars(select(Document).order_by(Document.created_at)).all()
        return {
            "documents": [
                {
                    "id": d.id,
                    "path": d.path,
                    "modality": d.modality,
                    "ingested": d.ingested,
                    "ingest_status": d.ingest_status,
                    "conflict_flag": d.conflict_flag,
                    "conflict_reason": d.conflict_reason,
                    "atom_count": d.atom_count,
                    "graph_projected_atom_count": d.graph_projected_atom_count,
                    "graph_projection_status": d.graph_projection_status,
                }
                for d in docs
            ]
        }
    finally:
        session.close()


@router.get("/documents/{document_id}", dependencies=[Depends(_require_auth("viewer"))])
def get_document(document_id: str, request: Request) -> dict:
    session = _session(request)
    try:
        doc = session.get(Document, document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return {
            "id": doc.id,
            "path": doc.path,
            "title": doc.title,
            "modality": doc.modality,
            "ingested": doc.ingested,
            "ingest_status": doc.ingest_status,
            "conflict_flag": doc.conflict_flag,
            "conflict_reason": doc.conflict_reason,
            "atom_count": doc.atom_count,
            "graph_projected_atom_count": doc.graph_projected_atom_count,
            "graph_projection_status": doc.graph_projection_status,
            "provenance": doc.provenance,
        }
    finally:
        session.close()


@router.get("/auth/whoami")
def auth_whoami(request: Request, auth_context: AuthContext = Depends(_require_auth("viewer"))) -> dict:
    allowed_modes = ["PUBLIC"]
    if request.app.state.auth_service.mode_allows(auth_context.role, "RAW", request.app.state.settings.raw_mode_enabled):
        allowed_modes.append("RAW")
    return {
        "api_key_id": auth_context.api_key_id,
        "owner": auth_context.owner,
        "role": auth_context.role,
        "allowed_modes": allowed_modes,
    }
