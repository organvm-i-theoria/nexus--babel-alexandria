# Nexus Babel Alexandria MVP-Next Roadmap

## Purpose

This roadmap is the execution-focused companion to `docs/roadmap.md`.

- `docs/roadmap.md`: long-horizon RLOS / Theoria architecture vision
- `docs/roadmap_mvp_next.md`: near-term hardening and acceleration work for the current codebase

The goal is to improve reliability, developer velocity, and extension readiness without claiming full RLOS implementation.

## Current Baseline (2026-02-25)

- FastAPI service + worker + Alembic migrations are implemented
- `28` `/api/v1` operations are available
- Contract + integration + logic tests are green (`82` tests before hardening additions)
- Major maintainability hotspots are the API route surface and large service modules (`ingestion.py`, `remix.py`)

## Phase 1 — Trust and Operational Hardening

### 1.1 Runtime Safety Defaults

Targets:
- `src/nexus_babel/config.py`
- `src/nexus_babel/main.py`
- `src/nexus_babel/db.py`
- `tests/test_hardening_runtime.py`

Outcomes:
- Environment-aware schema startup modes (`auto_create`, `migrate_only`, `off`)
- Environment-aware bootstrap API key seeding (`NEXUS_BOOTSTRAP_KEYS_ENABLED`)
- Non-dev warnings for cwd-derived storage paths
- Tests covering prod startup behavior and request ID preservation on errors

### 1.2 Docs and Operator Accuracy

Targets:
- `README.md`
- `docs/OPERATOR_RUNBOOK.md`
- `.env.example`
- `Makefile`

Outcomes:
- MVP vs planned claims explicitly separated
- Runbook commands executable (`make db-upgrade`, `make test`, `make lint`)
- Production guidance for schema and bootstrap settings

## Phase 2 — API Maintainability and Contract Stability

### 2.1 Route Modularization (Completed in this hardening wave)

Targets:
- `src/nexus_babel/api/routes/`
- `src/nexus_babel/api/deps.py`
- `src/nexus_babel/api/errors.py`

Outcomes:
- Domain routers replace monolithic `api/routes.py`
- Shared auth/session/mode enforcement helpers
- Standardized exception mapping helpers and domain error types
- Route parity validation via tests/OpenAPI operation-count checks

### 2.2 Contract Governance (Next)

Targets:
- `tests/test_hardening_runtime.py` (extend)
- `tests/test_ab_plan_01.py`
- optional `scripts/check_openapi_contract.py`

Outcomes:
- OpenAPI snapshot or normalized operation registry check
- Error payload compatibility checks (`detail` retained)
- Route/module parity guardrails during future refactors

## Phase 3 — CI and Developer Velocity

### 3.1 Quality Gate Expansion

Targets:
- `.github/workflows/ci-minimal.yml`
- `pyproject.toml`

Outcomes:
- `ruff` lint gate in CI
- `compileall` syntax sanity gate
- CI and local commands aligned via `Makefile`

### 3.2 Optional Next Gates (Deferred)

Candidates:
- type checking (`mypy` or `pyright`)
- dependency audit / vulnerability scan
- docs consistency smoke checks in CI

Deferred until a type policy and acceptable false-positive tolerance are defined.

## Phase 4 — Service Boundary Cleanup (Acceleration)

### 4.1 Remix Service Decomposition

Primary target:
- `src/nexus_babel/services/remix.py`

Extractable units:
- strategy implementations
- artifact serialization/mapping
- lineage graph ref construction
- context resolution and atom-level selection helpers

Success criteria:
- `compose()` and `remix()` signatures unchanged
- existing remix tests remain green
- reduced file size and improved unit test granularity

### 4.2 Ingestion Service Decomposition

Primary target:
- `src/nexus_babel/services/ingestion.py`

Extractable units:
- modality detection and media metadata adapters
- text/pdf extraction and segmentation helpers
- atom/projection ledger routines
- cross-modal linking helpers

Success criteria:
- `ingest_batch()` and `get_job_status()` signatures unchanged
- ingestion contract tests remain green
- projection/canonicalization semantics preserved

## Phase 5 — MVP-Next Feature Extensions (After Hardening)

Candidates to accelerate once boundaries are cleaner:
- richer plugin providers beyond `ml_stub`
- stronger audit/report generation automation (`docs/certainty/*` as CI artifact)
- more explicit graph/query contracts and integrity verification modes
- operator-facing health/report endpoints (non-breaking additive)

## Non-Goals (This MVP-Next Roadmap)

- Full implementation of the 9-layer RLOS roadmap in `docs/roadmap.md`
- Auth redesign to OAuth/JWT and enterprise identity integration
- Cross-repo orchestration automation for organ dependencies
- Rewriting core persistence models or public `/api/v1` contracts without compatibility planning
