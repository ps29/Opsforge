from pathlib import Path

import pytest

from opsforge import db
from opsforge.models import JobStatus
from opsforge.repository import create_report_job, get_report_job, retry_report_job
from opsforge.worker import run_once


@pytest.fixture()
def database(tmp_path: Path):
    db.configure_database(f"sqlite:///{tmp_path / 'worker.db'}")
    db.init_db()
    yield


def test_worker_processes_pending_job(database) -> None:
    with db.session_scope() as session:
        job = create_report_job(session, {"title": "Error budget", "owner": "sre", "data": {"burn": 4}})
        job_id = job.id

    assert run_once() is True

    with db.session_scope() as session:
        processed = get_report_job(session, job_id)
        assert processed is not None
        assert processed.status == JobStatus.succeeded.value
        assert processed.attempts == 1
        assert processed.output["numeric_total"] == 4


def test_worker_marks_invalid_job_failed(database) -> None:
    with db.session_scope() as session:
        job = create_report_job(session, {"title": "Bad report", "owner": "sre", "data": [], "force_fail": False})
        job_id = job.id

    assert run_once() is True

    with db.session_scope() as session:
        failed = get_report_job(session, job_id)
        assert failed is not None
        assert failed.status == JobStatus.failed.value
        assert failed.failure_reason == "data must be a JSON object"


def test_worker_is_idempotent_for_succeeded_job(database) -> None:
    with db.session_scope() as session:
        job = create_report_job(session, {"title": "Idempotency", "owner": "sre", "data": {"a": 1}})
        job_id = job.id

    assert run_once() is True
    assert run_once() is False

    with db.session_scope() as session:
        processed = get_report_job(session, job_id)
        assert processed is not None
        assert processed.status == JobStatus.succeeded.value
        assert processed.attempts == 1


def test_failed_job_can_be_retried_without_duplicate(database) -> None:
    with db.session_scope() as session:
        job = create_report_job(session, {"title": "Retry", "owner": "sre", "data": {}, "force_fail": True})
        job_id = job.id

    assert run_once() is True

    with db.session_scope() as session:
        failed = get_report_job(session, job_id)
        assert failed is not None
        failed.payload = {**failed.payload, "force_fail": False}
        retried = retry_report_job(session, failed)
        assert retried.status == JobStatus.pending.value

    assert run_once() is True

    with db.session_scope() as session:
        processed = get_report_job(session, job_id)
        assert processed is not None
        assert processed.status == JobStatus.succeeded.value
        assert processed.attempts == 2
