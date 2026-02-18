from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from nexus_babel.main import app


if __name__ == "__main__":
    root = Path.cwd()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/ingest/batch",
            json={
                "source_paths": [str(path) for path in sorted(root.iterdir()) if path.is_file()],
                "modalities": [],
                "parse_options": {"atomize": True},
            },
        )
        response.raise_for_status()
        payload = response.json()
        print("Ingest job created:", payload)
        job = client.get(f"/api/v1/ingest/jobs/{payload['ingest_job_id']}")
        job.raise_for_status()
        print("Job status:", job.json())
