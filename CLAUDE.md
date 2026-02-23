# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

**Nexus Babel Alexandria** (aka "Theoria Linguae Machina") is an NLP corpus management and analysis platform. It ingests multimodal documents (text, PDF, image, audio), atomizes them into hierarchical units, projects them into a knowledge graph, and provides multi-layer linguistic analysis with dual-mode governance (PUBLIC/RAW).

## Build & Run

Requires Python >=3.11.

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"              # dev includes pytest, httpx, alembic
pip install -e ".[dev,postgres]"     # add PostgreSQL support

# Dev server (defaults to SQLite, binds 0.0.0.0:8000)
make dev                             # uvicorn on :8000 with --reload

# Tests
make test                            # pytest -q
pytest tests/test_mvp.py -v          # MVP test suite
pytest tests/test_wave2.py -v        # Wave-2 async jobs/evolution tests
pytest tests/test_mvp.py::test_ingestion_completeness -v  # single test

# Database migrations (Alembic, targets SQLite by default via alembic.ini)
make db-upgrade                      # alembic upgrade head

# Background worker (processes async jobs from the jobs table)
make worker                          # python -m nexus_babel.worker
python -m nexus_babel.worker --once  # process one job and exit

# Corpus ingestion script
make ingest                          # python scripts/ingest_corpus.py

# Docker services (Postgres + Neo4j for production-like local dev)
docker compose up -d

# Other scripts
python scripts/load_test.py          # baseline load test
python scripts/repo_certainty_audit.py  # repo certainty audit
```

No linter or type checker is configured in pyproject.toml yet. CI (`ci-minimal.yml`) only validates repo structure (README exists, markdown files present) — it does not run tests or lint.

## Environment

Copy `.env.example` to `.env`. All settings use the `NEXUS_` prefix (handled by `pydantic-settings`). Key variables:

- `NEXUS_DATABASE_URL` — SQLite by default (`sqlite:///./nexus_babel.db`), PostgreSQL for docker
- `NEXUS_NEO4J_URI` / `NEXUS_NEO4J_USERNAME` / `NEXUS_NEO4J_PASSWORD` — optional; without Neo4j, the hypergraph uses an in-memory `LocalGraphCache`
- `NEXUS_RAW_MODE_ENABLED` — toggles RAW mode access
- `NEXUS_ASYNC_JOBS_ENABLED` — toggles async job submission
- `NEXUS_BOOTSTRAP_*_KEY` — dev API keys seeded at startup for viewer/operator/researcher/admin roles

## Architecture

### Application Factory

`create_app()` in `main.py` builds the FastAPI app, wires all services onto `app.state`, and seeds default API keys + governance policies in the lifespan handler. A module-level `app = create_app()` is used by uvicorn. Tests use `create_app(settings_override)` with an isolated SQLite + tmp_path.

### Source Layout

```
src/nexus_babel/
  main.py              # FastAPI app factory, middleware, health/metrics endpoints, frontend shell
  config.py            # Settings (pydantic-settings, NEXUS_ prefix, .env file)
  db.py                # DBManager — SQLAlchemy engine + sessionmaker wrapper
  models.py            # All ORM models (SQLAlchemy 2.0 mapped_column style)
  schemas.py           # Pydantic request/response models for the API
  worker.py            # Polling async job worker (CLI entrypoint)
  api/
    routes.py          # All /api/v1/ endpoints (single router)
  services/
    auth.py            # API key auth, role hierarchy (viewer < operator < researcher < admin)
    ingestion.py       # Multi-modal ingestion pipeline (text/PDF/image/audio)
    analysis.py        # 9-layer linguistic analysis (token → semiotic)
    evolution.py       # Branch evolution: natural_drift, synthetic_mutation, phase_shift, glyph_fusion
    governance.py      # Dual-mode content governance (PUBLIC blocks, RAW flags)
    hypergraph.py      # Neo4j graph projection + local cache fallback
    jobs.py            # Async job queue: submit/lease/execute/retry with backoff
    plugins.py         # Plugin registry with deterministic + ML stub providers
    rhetoric.py        # Rhetorical analysis (ethos/pathos/logos scoring, fallacy detection)
    canonicalization.py # Document variant linking (sibling representations, semantic equivalence)
    text_utils.py      # Atomization (glyph-seed/word/sentence/paragraph), conflict detection
    metrics.py         # In-memory counters + timing histograms
```

### Core Data Flow

1. **Ingest** (`POST /api/v1/ingest/batch`) — files resolved against `corpus_root`, checksummed, parsed by modality, atomized into 4 levels, projected to hypergraph, canonicalization applied
2. **Analyze** (`POST /api/v1/analyze`) — runs 9 linguistic analysis layers (token, morphology, syntax, semantics, pragmatics, discourse, sociolinguistics, rhetoric, semiotic) against a document or branch, through the plugin chain
3. **Evolve** (`POST /api/v1/evolve/branch`) — creates branching text evolution (natural_drift, synthetic_mutation, phase_shift, glyph_fusion) with deterministic replay via seeded RNG
4. **Governance** (`POST /api/v1/governance/evaluate`) — evaluates text against mode-specific policies; PUBLIC blocks on first hit, RAW allows with flagging

### Key Design Patterns

- **Dual-mode system**: PUBLIC mode enforces content filtering; RAW mode allows flagged terms for research. Mode access is controlled by both role level and per-key `raw_mode_enabled` flag.
- **Plugin chain**: Analysis layers run through a `PluginRegistry` with fallback chain (`ml_first` → `deterministic`, or `deterministic` only). Each layer produces output + confidence + provider provenance.
- **Hypergraph dual-write**: Document/atom projections write to both a `LocalGraphCache` (always) and Neo4j (when configured). Integrity checks compare both.
- **Async job queue**: Jobs table with lease-based execution, retry with exponential backoff (`[2, 10, 30]s`), idempotency keys, and artifact tracking. Worker polls and processes.
- **Branch evolution determinism**: Event processing uses seeded RNG derived from `sha256(event_type:seed:text_hash)`, ensuring identical inputs produce identical outputs for reproducible replay.

### Auth Model

Four roles in ascending order: `viewer` → `operator` → `researcher` → `admin`. API key auth via `X-Nexus-API-Key` header. Bootstrap keys are seeded at startup from settings.

### Database

SQLAlchemy 2.0 with `mapped_column`. SQLite for dev/test, PostgreSQL for docker. Key models: `Document`, `Atom`, `Branch`, `BranchEvent`, `AnalysisRun`, `LayerOutput`, `Job`, `JobAttempt`, `ModePolicy`, `PolicyDecision`, `AuditLog`, `ProjectionLedger`, `DocumentVariant`.

Alembic migrations in `alembic/versions/` (`20260218_0001_initial`, `20260218_0002_wave2_alpha`). The `alembic.ini` defaults to SQLite; for PostgreSQL, set `sqlalchemy.url` or use the `NEXUS_DATABASE_URL` env var in `alembic/env.py`.

### Testing Approach

Tests use `FastAPI.TestClient` with an isolated SQLite database per test via `tmp_path`. The `conftest.py` provides `test_settings`, `client`, `auth_headers` (all 4 roles), and `sample_corpus` (text, yaml, conflict yaml, PDF, image, WAV) fixtures.

## Routes

Non-API routes (no auth): `GET /healthz` (health check), `GET /metrics` (in-memory counters), `GET /app/{view}` (frontend shell for `corpus`, `hypergraph`, `timeline`, `governance`), `GET /` (redirects to `/app/corpus`).

### API Routes (all under `/api/v1`)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/ingest/batch` | operator | Ingest files from corpus |
| GET | `/ingest/jobs/{id}` | viewer | Check ingest job status |
| POST | `/analyze` | operator | Run linguistic analysis |
| GET | `/analysis/runs/{id}` | viewer | Get analysis run detail |
| GET | `/analysis/runs` | viewer | List analysis runs |
| POST | `/evolve/branch` | operator | Create branch evolution |
| GET | `/branches` | viewer | List branches |
| GET | `/branches/{id}/timeline` | viewer | Get branch event timeline |
| POST | `/branches/{id}/replay` | viewer | Replay branch to current state |
| GET | `/branches/{id}/compare/{other}` | viewer | Diff two branches |
| POST | `/governance/evaluate` | operator | Evaluate text against policies |
| POST | `/rhetorical_analysis` | operator | Ethos/pathos/logos analysis |
| POST | `/jobs/submit` | operator | Submit async job |
| GET | `/jobs/{id}` | viewer | Check job status |
| GET | `/jobs` | viewer | List jobs |
| POST | `/jobs/{id}/cancel` | operator | Cancel queued job |
| GET | `/documents` | viewer | List all documents |
| GET | `/documents/{id}` | viewer | Get document detail |
| GET | `/hypergraph/query` | viewer | Query graph nodes/edges |
| GET | `/hypergraph/documents/{id}/integrity` | viewer | Verify graph consistency |
| GET | `/auth/whoami` | viewer | Current auth context |
| GET | `/audit/policy-decisions` | operator | List governance decisions |

<!-- ORGANVM:AUTO:START -->
## System Context (auto-generated — do not edit)

**Organ:** ORGAN-I (Theory) | **Tier:** archive | **Status:** ARCHIVED
**Org:** `unknown` | **Repo:** `nexus--babel-alexandria-`

### Edges
- **Produces** → `unknown`: unknown
- **Consumes** ← `organvm-i-theoria/linguistic-atomization-framework`: unknown

### Siblings in Theory
`recursive-engine--generative-entity`, `organon-noumenon--ontogenetic-morphe`, `auto-revision-epistemic-engine`, `narratological-algorithmic-lenses`, `call-function--ontological`, `sema-metra--alchemica-mundi`, `system-governance-framework`, `cognitive-archaelogy-tribunal`, `a-recursive-root`, `radix-recursiva-solve-coagula-redi`, `.github`, `reverse-engine-recursive-run`, `4-ivi374-F0Rivi4`, `cog-init-1-0-`, `collective-persona-operations` ... and 4 more

### Governance
- Foundational theory layer. No upstream dependencies.

*Last synced: 2026-02-19T00:57:56Z*
<!-- ORGANVM:AUTO:END -->
