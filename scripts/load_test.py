from __future__ import annotations

import time
from statistics import mean

from fastapi.testclient import TestClient

from nexus_babel.main import app


if __name__ == "__main__":
    durations: list[float] = []
    with TestClient(app) as client:
        docs = client.get("/api/v1/documents").json().get("documents", [])
        if not docs:
            raise SystemExit("No documents found. Run scripts/ingest_corpus.py first.")

        target = docs[0]["id"]
        for _ in range(25):
            start = time.perf_counter()
            resp = client.post("/api/v1/analyze", json={"document_id": target, "mode": "PUBLIC"})
            resp.raise_for_status()
            durations.append(time.perf_counter() - start)

    avg = mean(durations)
    p95 = sorted(durations)[int(len(durations) * 0.95) - 1]
    print(f"avg={avg:.4f}s p95={p95:.4f}s")
