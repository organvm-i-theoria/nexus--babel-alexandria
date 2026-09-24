from __future__ import annotations

import pytest
from sqlalchemy import select

from nexus_babel.main import _initialize_schema_and_seeds, create_app
from nexus_babel.models import Job
from nexus_babel.worker import run_worker


@pytest.fixture
def worker_app(test_settings):
    app = create_app(test_settings)
    _initialize_schema_and_seeds(app)
    return app


def test_run_worker_once_no_jobs(worker_app):
    processed = run_worker(once=True, app=worker_app)
    assert processed == 0


def test_run_worker_once_one_job(worker_app):
    session = worker_app.state.db.session()
    try:
        job = worker_app.state.job_service.submit(session, job_type="integrity_audit", payload={})
        session.commit()
        job_id = job.id
    finally:
        session.close()

    processed = run_worker(once=True, app=worker_app)
    assert processed == 1

    session = worker_app.state.db.session()
    try:
        updated_job = session.scalar(select(Job).where(Job.id == job_id))
        assert updated_job is not None
        assert updated_job.status == "succeeded"
    finally:
        session.close()


def test_run_worker_max_jobs(worker_app):
    session = worker_app.state.db.session()
    try:
        for _ in range(5):
            worker_app.state.job_service.submit(session, job_type="integrity_audit", payload={})
        session.commit()
    finally:
        session.close()

    processed = run_worker(max_jobs=3, app=worker_app)
    assert processed == 3

    session = worker_app.state.db.session()
    try:
        queued = session.scalars(select(Job).where(Job.status == "queued")).all()
        assert len(queued) == 2
        succeeded = session.scalars(select(Job).where(Job.status == "succeeded")).all()
        assert len(succeeded) == 3
    finally:
        session.close()


def test_run_worker_stale_lease_failure_propagates_and_rolls_back(worker_app, monkeypatch):
    rollback_called = False
    close_called = False

    def failing_complete_stale_leases(session, worker_name):
        raise RuntimeError("Stale lease recovery unexpected failure")

    monkeypatch.setattr(worker_app.state.job_service, "complete_stale_leases", failing_complete_stale_leases)

    original_session_factory = worker_app.state.db.session

    def mock_session_factory():
        s = original_session_factory()
        original_rollback = s.rollback
        original_close = s.close

        def tracking_rollback():
            nonlocal rollback_called
            rollback_called = True
            return original_rollback()

        def tracking_close():
            nonlocal close_called
            close_called = True
            return original_close()

        s.rollback = tracking_rollback
        s.close = tracking_close
        return s

    monkeypatch.setattr(worker_app.state.db, "session", mock_session_factory)

    with pytest.raises(RuntimeError, match="Stale lease recovery unexpected failure"):
        run_worker(once=True, app=worker_app)

    assert rollback_called
    assert close_called


def test_run_worker_commit_failure_propagates_and_rolls_back(worker_app, monkeypatch):
    session = worker_app.state.db.session()
    try:
        worker_app.state.job_service.submit(session, job_type="integrity_audit", payload={})
        session.commit()
    finally:
        session.close()

    original_session_factory = worker_app.state.db.session

    rollback_called = False
    close_called = False

    def mock_session_factory():
        s = original_session_factory()
        original_rollback = s.rollback
        original_close = s.close

        def failing_commit():
            raise RuntimeError("Commit failed unexpectedly")

        def tracking_rollback():
            nonlocal rollback_called
            rollback_called = True
            return original_rollback()

        def tracking_close():
            nonlocal close_called
            close_called = True
            return original_close()

        s.commit = failing_commit
        s.rollback = tracking_rollback
        s.close = tracking_close
        return s

    monkeypatch.setattr(worker_app.state.db, "session", mock_session_factory)

    with pytest.raises(RuntimeError, match="Commit failed unexpectedly"):
        run_worker(once=True, app=worker_app)

    assert rollback_called
    assert close_called
