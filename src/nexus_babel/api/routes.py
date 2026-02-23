from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_babel.models import AnalysisRun, Branch, Document, Job
from nexus_babel.services.auth import AuthContext
from nexus_babel.schemas import (
    AnalysisRunResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    BranchCompareResponse,
    BranchEventView,
    BranchReplayResponse,
    BranchTimelineResponse,
    EvolveBranchRequest,
    EvolveBranchResponse,
    GovernanceEvaluateRequest,
    GovernanceEvaluateResponse,
    JobStatusResponse,
    JobSubmitRequest,
    JobSubmitResponse,
    IngestBatchRequest,
    IngestBatchResponse,
    IngestFileStatus,
    IngestJobResponse,
    RemixRequest,
    RemixResponse,
    RhetoricalAnalysisRequest,
    RhetoricalAnalysisResponse,
    SeedProvisionRequest,
    SeedProvisionResponse,
    SeedTextEntry,
    SeedTextListResponse,
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
    if not request.app.state.auth_service.mode_allows(
        ctx.role,
        mode,
        request.app.state.settings.raw_mode_enabled,
        ctx.raw_mode_enabled,
    ):
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
            documents_unchanged=result.get("documents_unchanged", 0),
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
            documents_unchanged=result.get("documents_unchanged", 0),
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
        if payload.execution_mode == "async":
            if not request.app.state.settings.async_jobs_enabled:
                raise HTTPException(status_code=400, detail="Async jobs are disabled by feature flag")
            job = request.app.state.job_service.submit(
                session=session,
                job_type="analyze",
                payload={
                    "document_id": payload.document_id,
                    "branch_id": payload.branch_id,
                    "layers": payload.layers,
                    "mode": payload.mode,
                    "plugin_profile": payload.plugin_profile,
                },
                execution_mode="async",
                created_by=auth_context.owner,
            )
            session.commit()
            return AnalyzeResponse(
                analysis_run_id=None,
                mode=payload.mode,
                layers={},
                confidence_bundle={},
                hypergraph_ids={},
                plugin_provenance={},
                job_id=job.id,
                status=job.status,
            )

        run, result = request.app.state.analysis_service.analyze(
            session=session,
            document_id=payload.document_id,
            branch_id=payload.branch_id,
            layers=payload.layers,
            mode=payload.mode,
            execution_mode="sync",
            plugin_profile=payload.plugin_profile,
            job_id=None,
        )

        shadow_job_id = None
        if payload.execution_mode == "shadow" and request.app.state.settings.shadow_execution_enabled:
            shadow_job = request.app.state.job_service.submit(
                session=session,
                job_type="analyze",
                payload={
                    "document_id": payload.document_id,
                    "branch_id": payload.branch_id,
                    "layers": payload.layers,
                    "mode": payload.mode,
                    "plugin_profile": payload.plugin_profile or "ml_first",
                },
                execution_mode="async",
                created_by=auth_context.owner,
            )
            shadow_job_id = shadow_job.id

        session.commit()
        return AnalyzeResponse(
            analysis_run_id=run.id,
            mode=result["mode"],
            layers=result["layers"],
            confidence_bundle=result["confidence_bundle"],
            hypergraph_ids=result["hypergraph_ids"],
            plugin_provenance=result.get("plugin_provenance", {}),
            job_id=shadow_job_id,
            status="completed" if not shadow_job_id else "shadow_queued",
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


@router.get("/branches", dependencies=[Depends(_require_auth("viewer"))])
def list_branches(request: Request, limit: int = Query(default=100, ge=1, le=1000)) -> dict:
    session = _session(request)
    try:
        branches = session.scalars(select(Branch).order_by(Branch.created_at.desc()).limit(limit)).all()
        return {
            "branches": [
                {
                    "id": b.id,
                    "parent_branch_id": b.parent_branch_id,
                    "root_document_id": b.root_document_id,
                    "mode": b.mode,
                    "branch_version": b.branch_version,
                    "created_at": b.created_at,
                }
                for b in branches
            ]
        }
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
            decision_trace=decision.get("decision_trace", {}),
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
                    "modality_status": d.modality_status,
                    "provider_summary": d.provider_summary,
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
            "modality_status": doc.modality_status,
            "provider_summary": doc.provider_summary,
            "provenance": doc.provenance,
        }
    finally:
        session.close()


@router.get("/auth/whoami")
def auth_whoami(request: Request, auth_context: AuthContext = Depends(_require_auth("viewer"))) -> dict:
    allowed_modes = ["PUBLIC"]
    if request.app.state.auth_service.mode_allows(
        auth_context.role,
        "RAW",
        request.app.state.settings.raw_mode_enabled,
        auth_context.raw_mode_enabled,
    ):
        allowed_modes.append("RAW")
    return {
        "api_key_id": auth_context.api_key_id,
        "owner": auth_context.owner,
        "role": auth_context.role,
        "raw_mode_enabled": auth_context.raw_mode_enabled,
        "allowed_modes": allowed_modes,
    }


@router.post("/jobs/submit", response_model=JobSubmitResponse)
def submit_job(
    payload: JobSubmitRequest,
    request: Request,
    auth_context: AuthContext = Depends(_require_auth("operator")),
) -> JobSubmitResponse:
    session = _session(request)
    try:
        if payload.job_type == "analyze":
            mode = str(payload.payload.get("mode", "PUBLIC"))
            _enforce_mode(request, auth_context, mode)
        if payload.execution_mode == "async" and not request.app.state.settings.async_jobs_enabled:
            raise HTTPException(status_code=400, detail="Async jobs are disabled by feature flag")
        job = request.app.state.job_service.submit(
            session=session,
            job_type=payload.job_type,
            payload=payload.payload,
            execution_mode=payload.execution_mode,
            idempotency_key=payload.idempotency_key,
            created_by=auth_context.owner,
            max_attempts=payload.max_attempts,
        )
        if payload.execution_mode == "sync":
            request.app.state.job_service.execute(session, job)
        session.commit()
        return JobSubmitResponse(
            job_id=job.id,
            status=job.status,
            job_type=job.job_type,
            execution_mode=job.execution_mode,  # type: ignore[arg-type]
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        session.close()


@router.get("/jobs/{job_id}", response_model=JobStatusResponse, dependencies=[Depends(_require_auth("viewer"))])
def get_job(job_id: str, request: Request) -> JobStatusResponse:
    session = _session(request)
    try:
        data = request.app.state.job_service.get_job(session=session, job_id=job_id)
        return JobStatusResponse(**data)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        session.close()


@router.get("/jobs", dependencies=[Depends(_require_auth("viewer"))])
def list_jobs(request: Request, limit: int = Query(default=100, ge=1, le=1000)) -> dict:
    session = _session(request)
    try:
        jobs = session.scalars(select(Job).order_by(Job.created_at.desc()).limit(limit)).all()
        return {
            "jobs": [
                {
                    "job_id": j.id,
                    "job_type": j.job_type,
                    "status": j.status,
                    "execution_mode": j.execution_mode,
                    "attempt_count": j.attempt_count,
                    "max_attempts": j.max_attempts,
                    "created_at": j.created_at,
                    "updated_at": j.updated_at,
                }
                for j in jobs
            ]
        }
    finally:
        session.close()


@router.post("/jobs/{job_id}/cancel", response_model=JobStatusResponse)
def cancel_job(
    job_id: str,
    request: Request,
    auth_context: AuthContext = Depends(_require_auth("operator")),
) -> JobStatusResponse:
    session = _session(request)
    try:
        _ = auth_context
        request.app.state.job_service.cancel(session=session, job_id=job_id)
        session.commit()
        data = request.app.state.job_service.get_job(session=session, job_id=job_id)
        return JobStatusResponse(**data)
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        session.close()


@router.get("/analysis/runs/{run_id}", response_model=AnalysisRunResponse, dependencies=[Depends(_require_auth("viewer"))])
def analysis_run(run_id: str, request: Request) -> AnalysisRunResponse:
    session = _session(request)
    try:
        data = request.app.state.analysis_service.get_run(session=session, run_id=run_id)
        return AnalysisRunResponse(**data)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        session.close()


@router.get("/analysis/runs", dependencies=[Depends(_require_auth("viewer"))])
def list_analysis_runs(request: Request, limit: int = Query(default=100, ge=1, le=1000)) -> dict:
    session = _session(request)
    try:
        runs = session.scalars(select(AnalysisRun).order_by(AnalysisRun.created_at.desc()).limit(limit)).all()
        return {
            "runs": [
                {
                    "analysis_run_id": r.id,
                    "document_id": r.document_id,
                    "branch_id": r.branch_id,
                    "mode": r.mode,
                    "execution_mode": r.execution_mode,
                    "plugin_profile": r.plugin_profile,
                    "created_at": r.created_at,
                }
                for r in runs
            ]
        }
    finally:
        session.close()


@router.post("/branches/{branch_id}/replay", response_model=BranchReplayResponse, dependencies=[Depends(_require_auth("viewer"))])
def replay_branch(branch_id: str, request: Request) -> BranchReplayResponse:
    session = _session(request)
    try:
        data = request.app.state.evolution_service.replay_branch(session=session, branch_id=branch_id)
        return BranchReplayResponse(**data)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        session.close()


@router.get("/branches/{branch_id}/compare/{other_branch_id}", response_model=BranchCompareResponse, dependencies=[Depends(_require_auth("viewer"))])
def compare_branch(branch_id: str, other_branch_id: str, request: Request) -> BranchCompareResponse:
    session = _session(request)
    try:
        data = request.app.state.evolution_service.compare_branches(
            session=session,
            left_branch_id=branch_id,
            right_branch_id=other_branch_id,
        )
        return BranchCompareResponse(**data)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        session.close()


@router.get("/hypergraph/query", dependencies=[Depends(_require_auth("viewer"))])
def hypergraph_query(
    request: Request,
    document_id: str | None = Query(default=None),
    node_id: str | None = Query(default=None),
    relationship_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
) -> dict:
    return request.app.state.hypergraph.query(
        document_id=document_id,
        node_id=node_id,
        relationship_type=relationship_type,
        limit=limit,
    )


@router.get("/audit/policy-decisions", dependencies=[Depends(_require_auth("operator"))])
def audit_policy_decisions(request: Request, limit: int = Query(default=100, ge=1, le=1000)) -> dict:
    session = _session(request)
    try:
        return {"decisions": request.app.state.governance_service.list_policy_decisions(session=session, limit=limit)}
    finally:
        session.close()


@router.get("/corpus/seeds", response_model=SeedTextListResponse, dependencies=[Depends(_require_auth("viewer"))])
def list_seed_texts(request: Request) -> SeedTextListResponse:
    seeds = request.app.state.seed_corpus_service.list_seed_texts()
    return SeedTextListResponse(seeds=[SeedTextEntry(**s) for s in seeds])


@router.post("/corpus/seed", response_model=SeedProvisionResponse)
def provision_seed_text(
    payload: SeedProvisionRequest,
    request: Request,
    auth_context: AuthContext = Depends(_require_auth("admin")),
) -> SeedProvisionResponse:
    session = _session(request)
    try:
        _ = auth_context
        result = request.app.state.seed_corpus_service.provision_seed_text(payload.title)
        doc_id = None
        if result.get("local_path") and result["status"] in ("provisioned", "already_provisioned"):
            from pathlib import Path

            local_path = Path(result["local_path"])
            if local_path.exists():
                ingest_result = request.app.state.ingestion_service.ingest_batch(
                    session=session,
                    source_paths=[str(local_path)],
                    modalities=["text"],
                    parse_options={},
                )
                session.commit()
                files = ingest_result.get("files", [])
                if files:
                    doc_id = files[0].get("document_id")
        return SeedProvisionResponse(
            title=result["title"],
            status=result["status"],
            local_path=result.get("local_path"),
            document_id=doc_id,
        )
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        session.close()


@router.post("/remix", response_model=RemixResponse)
def remix(
    payload: RemixRequest,
    request: Request,
    auth_context: AuthContext = Depends(_require_auth("operator")),
) -> RemixResponse:
    session = _session(request)
    try:
        _enforce_mode(request, auth_context, payload.mode)
        branch, event = request.app.state.remix_service.remix(
            session=session,
            source_document_id=payload.source_document_id,
            source_branch_id=payload.source_branch_id,
            target_document_id=payload.target_document_id,
            target_branch_id=payload.target_branch_id,
            strategy=payload.strategy,
            seed=payload.seed,
            mode=payload.mode,
        )
        session.commit()
        return RemixResponse(
            new_branch_id=branch.id,
            event_id=event.id,
            strategy=payload.strategy,
            diff_summary=event.diff_summary,
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        session.close()
