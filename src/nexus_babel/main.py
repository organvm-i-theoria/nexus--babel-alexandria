from __future__ import annotations

import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from nexus_babel.api.routes import router as api_router
from nexus_babel.config import Settings, get_settings
from nexus_babel.db import DBManager
from nexus_babel.models import Base
from nexus_babel.services.analysis import AnalysisService
from nexus_babel.services.auth import AuthService
from nexus_babel.services.evolution import EvolutionService
from nexus_babel.services.governance import GovernanceService
from nexus_babel.services.hypergraph import HypergraphProjector
from nexus_babel.services.ingestion import IngestionService
from nexus_babel.services.jobs import JobService
from nexus_babel.services.metrics import MetricsService
from nexus_babel.services.plugins import PluginRegistry
from nexus_babel.services.rhetoric import RhetoricalAnalyzer


def create_app(settings_override: Settings | None = None) -> FastAPI:
    settings = settings_override or get_settings()
    templates = Jinja2Templates(directory="src/nexus_babel/frontend/templates")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.db.create_all(Base.metadata)
        session = app.state.db.session()
        try:
            app.state.auth_service.ensure_default_api_keys(
                session,
                [
                    ("dev-viewer", "viewer", settings.bootstrap_viewer_key, False),
                    ("dev-operator", "operator", settings.bootstrap_operator_key, False),
                    ("dev-researcher", "researcher", settings.bootstrap_researcher_key, True),
                    ("dev-admin", "admin", settings.bootstrap_admin_key, True),
                ],
            )
            app.state.governance_service.ensure_default_policies(session, settings.public_blocked_terms)
            session.commit()
        finally:
            session.close()
        yield
        app.state.hypergraph.close()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.state.settings = settings
    app.state.db = DBManager(settings.database_url)
    app.state.hypergraph = HypergraphProjector(settings.neo4j_uri, settings.neo4j_username, settings.neo4j_password)
    app.state.metrics = MetricsService()
    app.state.auth_service = AuthService()
    app.state.plugin_registry = PluginRegistry(ml_enabled=settings.plugin_ml_enabled)
    app.state.rhetorical_analyzer = RhetoricalAnalyzer()
    app.state.analysis_service = AnalysisService(app.state.rhetorical_analyzer, app.state.plugin_registry)
    app.state.governance_service = GovernanceService()
    app.state.evolution_service = EvolutionService()
    app.state.ingestion_service = IngestionService(settings=settings, hypergraph=app.state.hypergraph)
    app.state.job_service = JobService(
        settings=settings,
        ingestion_service=app.state.ingestion_service,
        analysis_service=app.state.analysis_service,
        evolution_service=app.state.evolution_service,
        hypergraph=app.state.hypergraph,
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        started = time.perf_counter()
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        app.state.metrics.observe("http.request.ms", elapsed_ms)
        app.state.metrics.inc(f"http.status.{response.status_code}")
        response.headers["X-Request-ID"] = request_id
        return response

    app.include_router(api_router)

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/app/corpus")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metrics")
    async def metrics() -> dict:
        return app.state.metrics.snapshot()

    @app.get("/app/{view}", response_class=HTMLResponse)
    async def app_view(view: str, request: Request) -> HTMLResponse:
        allowed = {"corpus", "hypergraph", "timeline", "governance"}
        if view not in allowed:
            return HTMLResponse("Not Found", status_code=404)
        return templates.TemplateResponse(request, "shell.html", {"view": view})

    return app


app = create_app()
