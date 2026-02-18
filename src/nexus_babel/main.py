from __future__ import annotations

from contextlib import asynccontextmanager

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
                    ("dev-viewer", "viewer", settings.bootstrap_viewer_key),
                    ("dev-operator", "operator", settings.bootstrap_operator_key),
                    ("dev-researcher", "researcher", settings.bootstrap_researcher_key),
                    ("dev-admin", "admin", settings.bootstrap_admin_key),
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
    app.state.auth_service = AuthService()
    app.state.rhetorical_analyzer = RhetoricalAnalyzer()
    app.state.analysis_service = AnalysisService(app.state.rhetorical_analyzer)
    app.state.governance_service = GovernanceService()
    app.state.evolution_service = EvolutionService()
    app.state.ingestion_service = IngestionService(settings=settings, hypergraph=app.state.hypergraph)

    app.include_router(api_router)

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/app/corpus")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/app/{view}", response_class=HTMLResponse)
    async def app_view(view: str, request: Request) -> HTMLResponse:
        allowed = {"corpus", "hypergraph", "timeline", "governance"}
        if view not in allowed:
            return HTMLResponse("Not Found", status_code=404)
        return templates.TemplateResponse(request, "shell.html", {"view": view})

    return app


app = create_app()
