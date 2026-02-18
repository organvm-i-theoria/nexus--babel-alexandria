# Nexus Babel-Alexandria MVP Operator Runbook

## 1. Environment

- Python 3.11+
- Optional services (recommended):
  - Postgres 16
  - Neo4j 5.x

Start infra:

```bash
docker compose up -d
```

Install app:

```bash
python3 -m pip install -e .[dev,postgres]
```

## 2. Configuration

Copy and edit:

```bash
cp .env.example .env
```

Important variables:

- `NEXUS_DATABASE_URL`
- `NEXUS_NEO4J_URI`
- `NEXUS_NEO4J_USERNAME`
- `NEXUS_NEO4J_PASSWORD`
- `NEXUS_CORPUS_ROOT`
- `NEXUS_OBJECT_STORAGE_ROOT`

## 3. Start Service

```bash
uvicorn nexus_babel.main:app --host 0.0.0.0 --port 8000 --reload
```

Health check:

```bash
curl http://localhost:8000/healthz
```

## 4. Ingest Corpus

```bash
python scripts/ingest_corpus.py
```

Or direct API call:

```bash
curl -X POST http://localhost:8000/api/v1/ingest/batch \
  -H 'Content-Type: application/json' \
  -d '{"source_paths":[],"modalities":[],"parse_options":{"atomize":true}}'
```

## 5. Verify System

- `GET /api/v1/documents`
- `GET /api/v1/ingest/jobs/{job_id}`
- `GET /app/corpus`

## 6. Governance Modes

- `PUBLIC`: hard blocks on blocked terms
- `RAW`: allows output but logs policy hits

Evaluate sample:

```bash
curl -X POST http://localhost:8000/api/v1/governance/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"candidate_output":"example text","mode":"PUBLIC"}'
```

## 7. Testing

```bash
pytest -q
python scripts/load_test.py
```

## 8. Known Constraints

- RLOS analysis layers are heuristic MVP implementations, not full ML models yet.
- Image OCR and advanced audio analysis are represented via metadata paths in this slice.
- `seed.yaml` conflict markers are intentionally flagged as non-ingestable until resolved.
