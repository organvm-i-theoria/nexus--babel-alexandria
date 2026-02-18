from __future__ import annotations

import os

from fastapi.testclient import TestClient

from nexus_babel.main import app


if __name__ == "__main__":
    api_key = os.environ.get("NEXUS_BOOTSTRAP_OPERATOR_KEY", "nexus-dev-operator-key")  # allow-secret
    headers = {"X-Nexus-API-Key": api_key}
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/ingest/batch",
            headers=headers,
            json={
                "source_paths": [],
                "modalities": [],
                "parse_options": {"atomize": True},
            },
        )
        response.raise_for_status()
        payload = response.json()
        print("Ingest job created:", payload)
        job = client.get(f"/api/v1/ingest/jobs/{payload['ingest_job_id']}", headers=headers)
        job.raise_for_status()
        print("Job status:", job.json())
