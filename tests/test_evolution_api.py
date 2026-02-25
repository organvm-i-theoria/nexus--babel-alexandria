from __future__ import annotations

import hashlib

from sqlalchemy import func, select

from nexus_babel.models import Branch, BranchEvent, Document


def _ingest_one(client, sample_corpus, headers) -> str:
    response = client.post(
        "/api/v1/ingest/batch",
        headers=headers,
        json={
            "source_paths": [str(sample_corpus["text"])],
            "modalities": [],
            "parse_options": {"atomize": True},
        },
    )
    assert response.status_code == 200, response.text
    job = client.get(f"/api/v1/ingest/jobs/{response.json()['ingest_job_id']}", headers=headers)
    assert job.status_code == 200, job.text
    return job.json()["files"][0]["document_id"]


def test_evolve_branch_reverse_drift_supported(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    response = client.post(
        "/api/v1/evolve/branch",
        headers=auth_headers["operator"],
        json={
            "root_document_id": doc_id,
            "event_type": "reverse_drift",
            "event_payload": {"seed": 0},
            "mode": "PUBLIC",
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["diff_summary"]["event"] == "reverse_drift"
    assert "reversals" in payload["diff_summary"]


def test_multi_evolve_chain(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    response = client.post(
        "/api/v1/evolve/multi",
        headers=auth_headers["operator"],
        json={
            "root_document_id": doc_id,
            "mode": "PUBLIC",
            "events": [
                {"event_type": "natural_drift", "event_payload": {"seed": 11}},
                {"event_type": "reverse_drift", "event_payload": {"seed": 11}},
                {"event_type": "phase_shift", "event_payload": {"phase": "peak", "seed": 1}},
                {"event_type": "synthetic_mutation", "event_payload": {"mutation_rate": 0.15, "seed": 5}},
            ],
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload["branch_ids"]) == 4
    assert len(payload["event_ids"]) == 4
    assert payload["final_branch_id"] == payload["branch_ids"][-1]
    assert payload["event_count"] == 4
    assert payload["final_text_hash"]
    assert payload["final_preview"]


def test_multi_evolve_empty_events_raises(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    response = client.post(
        "/api/v1/evolve/multi",
        headers=auth_headers["operator"],
        json={
            "root_document_id": doc_id,
            "mode": "PUBLIC",
            "events": [],
        },
    )
    assert response.status_code == 400, response.text
    assert "events must not be empty" in response.json()["detail"]


def test_multi_evolve_rollback_on_failure(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])

    session = client.app.state.db.session()
    try:
        before_branch_count = int(session.scalar(select(func.count(Branch.id))) or 0)
        before_event_count = int(session.scalar(select(func.count(BranchEvent.id))) or 0)
    finally:
        session.close()

    response = client.post(
        "/api/v1/evolve/multi",
        headers=auth_headers["operator"],
        json={
            "root_document_id": doc_id,
            "mode": "PUBLIC",
            "events": [
                {"event_type": "natural_drift", "event_payload": {"seed": 2}},
                {"event_type": "reverse_drift", "event_payload": {"seed": 2}},
                {"event_type": "synthetic_mutation", "event_payload": {"mutation_rate": 5.0, "seed": 2}},
            ],
        },
    )
    assert response.status_code == 400, response.text

    session = client.app.state.db.session()
    try:
        after_branch_count = int(session.scalar(select(func.count(Branch.id))) or 0)
        after_event_count = int(session.scalar(select(func.count(BranchEvent.id))) or 0)
    finally:
        session.close()

    assert after_branch_count == before_branch_count
    assert after_event_count == before_event_count


def test_multi_evolve_requires_operator(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    response = client.post(
        "/api/v1/evolve/multi",
        headers=auth_headers["viewer"],
        json={
            "root_document_id": doc_id,
            "mode": "PUBLIC",
            "events": [{"event_type": "natural_drift", "event_payload": {"seed": 0}}],
        },
    )
    assert response.status_code == 403, response.text


def test_multi_evolve_raw_mode_enforced(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    response = client.post(
        "/api/v1/evolve/multi",
        headers=auth_headers["operator"],
        json={
            "root_document_id": doc_id,
            "mode": "RAW",
            "events": [{"event_type": "natural_drift", "event_payload": {"seed": 0}}],
        },
    )
    assert response.status_code == 403, response.text


def test_checkpoint_accelerated_replay_correctness(client, sample_corpus, auth_headers, monkeypatch):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    service = client.app.state.evolution_service

    parent_branch_id = None
    for seed in range(20):
        response = client.post(
            "/api/v1/evolve/branch",
            headers=auth_headers["operator"],
            json={
                "root_document_id": doc_id if parent_branch_id is None else None,
                "parent_branch_id": parent_branch_id,
                "event_type": "natural_drift",
                "event_payload": {"seed": seed},
                "mode": "PUBLIC",
            },
        )
        assert response.status_code == 200, response.text
        parent_branch_id = response.json()["new_branch_id"]
    assert parent_branch_id is not None

    calls = {"count": 0}
    original_decompress = service._decompress_snapshot

    def _wrapped_decompress(payload: str):
        calls["count"] += 1
        return original_decompress(payload)

    monkeypatch.setattr(service, "_decompress_snapshot", _wrapped_decompress)

    timeline_resp = client.get(f"/api/v1/branches/{parent_branch_id}/timeline", headers=auth_headers["viewer"])
    assert timeline_resp.status_code == 200, timeline_resp.text
    timeline_payload = timeline_resp.json()
    assert len(timeline_payload["events"]) == 20
    assert timeline_payload["replay_snapshot"]["event_count"] == 20
    assert calls["count"] >= 1

    session = client.app.state.db.session()
    try:
        target_branch = session.scalar(select(Branch).where(Branch.id == parent_branch_id))
        assert target_branch is not None

        lineage = service._lineage(session, target_branch)
        events: list[BranchEvent] = []
        for node in lineage:
            events.extend(
                session.scalars(
                    select(BranchEvent).where(BranchEvent.branch_id == node.id).order_by(BranchEvent.event_index, BranchEvent.created_at)
                ).all()
            )

        root_text = ""
        if target_branch.root_document_id:
            doc = session.scalar(select(Document).where(Document.id == target_branch.root_document_id))
            assert doc is not None
            root_text = str((doc.provenance or {}).get("extracted_text", ""))

        replay_text = root_text
        for event in events:
            replay_text = service._apply_event(replay_text, event.event_type, event.event_payload).output_text

        expected_hash = hashlib.sha256(replay_text.encode("utf-8")).hexdigest()
    finally:
        session.close()

    assert timeline_payload["replay_snapshot"]["text_hash"] == expected_hash


def test_branch_visualization_endpoint(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])

    b1 = client.post(
        "/api/v1/evolve/branch",
        headers=auth_headers["operator"],
        json={"root_document_id": doc_id, "event_type": "natural_drift", "event_payload": {"seed": 1}, "mode": "PUBLIC"},
    )
    assert b1.status_code == 200, b1.text
    branch_1 = b1.json()["new_branch_id"]

    b2 = client.post(
        "/api/v1/evolve/branch",
        headers=auth_headers["operator"],
        json={
            "parent_branch_id": branch_1,
            "event_type": "phase_shift",
            "event_payload": {"phase": "peak", "seed": 2},
            "mode": "PUBLIC",
        },
    )
    assert b2.status_code == 200, b2.text
    branch_2 = b2.json()["new_branch_id"]

    b3 = client.post(
        "/api/v1/evolve/branch",
        headers=auth_headers["operator"],
        json={
            "parent_branch_id": branch_2,
            "event_type": "reverse_drift",
            "event_payload": {"seed": 3},
            "mode": "PUBLIC",
        },
    )
    assert b3.status_code == 200, b3.text
    target_branch = b3.json()["new_branch_id"]

    response = client.get(f"/api/v1/branches/{target_branch}/visualization", headers=auth_headers["viewer"])
    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["branch_id"] == target_branch
    assert payload["root_document_id"] == doc_id
    assert len(payload["nodes"]) == 3
    assert len(payload["edges"]) >= 2
    assert payload["summary"]["event_count"] == 3
    assert payload["summary"]["lineage_depth"] == 3
    assert all("event_type" in node for node in payload["nodes"])
    assert all("metadata" in node for node in payload["nodes"])
