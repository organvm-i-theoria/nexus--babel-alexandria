from __future__ import annotations

import time
from statistics import mean


def _ingest(client, paths):
    response = client.post(
        "/api/v1/ingest/batch",
        json={
            "source_paths": [str(p) for p in paths],
            "modalities": [],
            "parse_options": {"atomize": True},
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    job = client.get(f"/api/v1/ingest/jobs/{payload['ingest_job_id']}")
    assert job.status_code == 200
    return payload, job.json()


def test_ingestion_completeness(client, sample_corpus):
    payload, job = _ingest(client, [sample_corpus["text"], sample_corpus["clean_yaml"], sample_corpus["pdf"]])
    assert payload["documents_ingested"] == 3
    assert payload["atoms_created"] > 0
    assert len(payload["provenance_digest"]) == 64

    statuses = {item["status"] for item in job["files"]}
    assert statuses == {"ingested"}

    for entry in job["files"]:
        doc = client.get(f"/api/v1/documents/{entry['document_id']}")
        assert doc.status_code == 200
        detail = doc.json()
        assert detail["ingested"] is True
        assert "checksum" in detail["provenance"]


def test_conflict_hygiene(client, sample_corpus):
    _, job = _ingest(client, [sample_corpus["conflict_yaml"]])
    assert job["files"][0]["status"] == "conflict"

    listing = client.get("/api/v1/documents").json()["documents"]
    conflicted = [d for d in listing if d["path"].endswith("seed.yaml")]
    assert conflicted
    assert conflicted[0]["conflict_flag"] is True
    assert conflicted[0]["ingested"] is False


def test_hypergraph_integrity(client, sample_corpus):
    _, job = _ingest(client, [sample_corpus["text"]])
    doc_id = job["files"][0]["document_id"]

    integrity = client.get(f"/api/v1/hypergraph/documents/{doc_id}/integrity")
    assert integrity.status_code == 200
    payload = integrity.json()
    assert payload["document_nodes"] == 1
    assert payload["atom_nodes"] > 0
    assert payload["contains_edges"] == payload["atom_nodes"]


def test_dual_mode_regression(client):
    text = "This output says we should kill all nuance."

    public_decision = client.post("/api/v1/governance/evaluate", json={"candidate_output": text, "mode": "PUBLIC"})
    raw_decision = client.post("/api/v1/governance/evaluate", json={"candidate_output": text, "mode": "RAW"})

    assert public_decision.status_code == 200
    assert raw_decision.status_code == 200

    public_payload = public_decision.json()
    raw_payload = raw_decision.json()

    assert public_payload["allow"] is False
    assert raw_payload["allow"] is True
    assert "kill" in public_payload["policy_hits"]
    assert "kill" in raw_payload["policy_hits"]


def test_branch_determinism(client, sample_corpus):
    _, job = _ingest(client, [sample_corpus["text"]])
    doc_id = job["files"][0]["document_id"]

    req = {"root_document_id": doc_id, "event_type": "natural_drift", "event_payload": {"seed": 42}, "mode": "RAW"}
    b1 = client.post("/api/v1/evolve/branch", json=req)
    b2 = client.post("/api/v1/evolve/branch", json=req)

    assert b1.status_code == 200
    assert b2.status_code == 200

    t1 = client.get(f"/api/v1/branches/{b1.json()['new_branch_id']}/timeline").json()
    t2 = client.get(f"/api/v1/branches/{b2.json()['new_branch_id']}/timeline").json()

    assert t1["replay_snapshot"]["text_hash"] == t2["replay_snapshot"]["text_hash"]


def test_multimodal_linkage(client, sample_corpus):
    _, job = _ingest(client, [sample_corpus["text"], sample_corpus["image"], sample_corpus["audio"]])

    entries = {item["path"]: item for item in job["files"]}
    text_doc = client.get(f"/api/v1/documents/{entries[str(sample_corpus['text'])]['document_id']}").json()
    image_doc = client.get(f"/api/v1/documents/{entries[str(sample_corpus['image'])]['document_id']}").json()
    audio_doc = client.get(f"/api/v1/documents/{entries[str(sample_corpus['audio'])]['document_id']}").json()

    assert "segments" in text_doc["provenance"]
    assert "segments" in image_doc["provenance"]
    assert "segments" in audio_doc["provenance"]
    assert audio_doc["provenance"]["segments"].get("duration_seconds", 0) > 0

    analysis = client.post("/api/v1/analyze", json={"document_id": text_doc["id"], "mode": "PUBLIC"})
    assert analysis.status_code == 200
    assert "document_node_id" in analysis.json()["hypergraph_ids"]


def test_rhetorical_output(client):
    response = client.post(
        "/api/v1/rhetorical_analysis",
        json={"text": "According to experts, therefore this proof is valid. Everyone knows this creates fear and hope."},
    )
    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"ethos_score", "pathos_score", "logos_score", "strategies", "fallacies", "explainability"}
    assert isinstance(payload["strategies"], list)


def test_api_contract_validation(client):
    bad_analyze = client.post("/api/v1/analyze", json={"mode": "PUBLIC"})
    assert bad_analyze.status_code == 400

    bad_branch = client.post("/api/v1/evolve/branch", json={"event_type": "phase_shift", "event_payload": {"phase": "compression"}})
    assert bad_branch.status_code == 400


def test_ui_e2e_flow(client, sample_corpus):
    for page in ["corpus", "hypergraph", "timeline", "governance"]:
        res = client.get(f"/app/{page}")
        assert res.status_code == 200

    _, job = _ingest(client, [sample_corpus["text"]])
    doc_id = job["files"][0]["document_id"]

    analyze = client.post("/api/v1/analyze", json={"document_id": doc_id, "mode": "PUBLIC"})
    assert analyze.status_code == 200

    evolve = client.post(
        "/api/v1/evolve/branch",
        json={"root_document_id": doc_id, "event_type": "phase_shift", "event_payload": {"phase": "compression", "seed": 7}, "mode": "RAW"},
    )
    assert evolve.status_code == 200

    branch_id = evolve.json()["new_branch_id"]
    timeline = client.get(f"/api/v1/branches/{branch_id}/timeline")
    assert timeline.status_code == 200

    policy = client.post("/api/v1/governance/evaluate", json={"candidate_output": "clean output", "mode": "PUBLIC"})
    assert policy.status_code == 200


def test_load_baseline(client, sample_corpus):
    _, job = _ingest(client, [sample_corpus["text"]])
    doc_id = job["files"][0]["document_id"]

    durations = []
    for _ in range(20):
        start = time.perf_counter()
        res = client.post("/api/v1/analyze", json={"document_id": doc_id, "mode": "PUBLIC"})
        assert res.status_code == 200
        durations.append(time.perf_counter() - start)

    assert mean(durations) < 1.5
