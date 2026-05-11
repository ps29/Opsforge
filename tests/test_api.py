from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from opsforge import db
from opsforge.main import create_app
from opsforge.models import JobStatus


@pytest.fixture()
def client(tmp_path: Path):
    db.configure_database(f"sqlite:///{tmp_path / 'test.db'}")
    db.init_db()
    with TestClient(create_app()) as test_client:
        yield test_client


def test_health_endpoints(client: TestClient) -> None:
    assert client.get("/health/live").status_code == 200
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_create_and_get_report(client: TestClient) -> None:
    create_response = client.post(
        "/reports",
        json={"title": "Daily latency report", "owner": "platform", "data": {"p95": 180, "errors": 2}},
    )
    assert create_response.status_code == 202
    body = create_response.json()
    assert body["status"] == JobStatus.pending.value

    get_response = client.get(f"/reports/{body['id']}")
    assert get_response.status_code == 200
    report = get_response.json()
    assert report["status"] == JobStatus.pending.value
    assert report["attempts"] == 0
    assert report["input_summary"] == "title=Daily latency report; owner=platform; fields=2"


def test_retry_only_works_for_failed_jobs(client: TestClient) -> None:
    create_response = client.post(
        "/reports",
        json={"title": "Capacity report", "owner": "sre", "data": {"nodes": 3}},
    )
    job_id = create_response.json()["id"]

    response = client.post(f"/jobs/{job_id}/retry")
    assert response.status_code == 409


def test_metrics_are_prometheus_text(client: TestClient) -> None:
    client.post("/reports", json={"title": "Metrics report", "owner": "sre", "data": {}})
    response = client.get("/metrics")
    assert response.status_code == 200
    assert 'opsforge_jobs_total{status="pending"} 1' in response.text
