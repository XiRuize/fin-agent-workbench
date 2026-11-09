from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(str(tmp_path / "test.db")))


def payload(**overrides):
    data = {
        "thesis": "储能出货超预期将带动 2027 年毛利修复",
        "confidence": 0.62,
        "evidence_for": [
            {
                "source_id": "S-18",
                "locator": "p.42",
                "quote": "2026H1 储能出货同比增长 58%",
            }
        ],
        "evidence_against": [
            {
                "source_id": "S-21",
                "locator": "p.7",
                "quote": "海外订单增速低于预期",
            }
        ],
        "falsifiers": ["2026Q4 储能毛利率 < 18%"],
        "valuation_impact": {
            "metric": "target_price",
            "from": 238,
            "to": 268,
        },
        "created_by": "agent:valuation",
    }
    data.update(overrides)
    return data


def create(client: TestClient, **overrides) -> dict:
    response = client.post("/api/v1/hypotheses", json=payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "service": "fin-agent-domain",
        "version": "0.1.0",
    }


def test_create_and_get(client: TestClient) -> None:
    created = create(client)
    assert created["id"].startswith("h_")
    assert created["status"] == "draft"
    assert created["valuation_impact"] == {
        "metric": "target_price",
        "from": 238.0,
        "to": 268.0,
    }

    response = client.get(f"/api/v1/hypotheses/{created['id']}")
    assert response.status_code == 200
    assert response.json()["thesis"] == created["thesis"]


def test_full_approval_flow(client: TestClient) -> None:
    created = create(client)
    hypothesis_id = created["id"]
    targets = ["submitted", "under_review", "approved", "frozen"]

    for target in targets:
        response = client.post(
            f"/api/v1/hypotheses/{hypothesis_id}/transitions",
            json={
                "to_status": target,
                "actor": "user:alice",
                "reason": f"move to {target}",
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["hypothesis"]["status"] == target

    events = client.get(
        f"/api/v1/hypotheses/{hypothesis_id}/events"
    ).json()
    assert [event["to_status"] for event in events] == targets
    assert all(event["actor"] == "user:alice" for event in events)


def test_invalid_transition_is_rejected(client: TestClient) -> None:
    created = create(client)
    response = client.post(
        f"/api/v1/hypotheses/{created['id']}/transitions",
        json={
            "to_status": "approved",
            "actor": "user:alice",
            "reason": "skip review",
        },
    )
    assert response.status_code == 409
    assert "draft -> approved" in response.json()["detail"]


def test_submission_requires_falsifier(client: TestClient) -> None:
    created = create(client, falsifiers=[])
    response = client.post(
        f"/api/v1/hypotheses/{created['id']}/transitions",
        json={
            "to_status": "submitted",
            "actor": "agent:valuation",
            "reason": "ready for review",
        },
    )
    assert response.status_code == 409
    assert "falsifier" in response.json()["detail"]


def test_list_filter(client: TestClient) -> None:
    first = create(client)
    create(client)
    assert len(client.get("/api/v1/hypotheses").json()) == 2

    response = client.post(
        f"/api/v1/hypotheses/{first['id']}/transitions",
        json={"to_status": "submitted", "actor": "agent:lead"},
    )
    assert response.status_code == 200

    submitted = client.get(
        "/api/v1/hypotheses", params={"status": "submitted"}
    ).json()
    assert [item["id"] for item in submitted] == [first["id"]]

    drafts = client.get("/api/v1/hypotheses", params={"status": "draft"}).json()
    assert len(drafts) == 1


def test_not_found(client: TestClient) -> None:
    assert client.get("/api/v1/hypotheses/h_missing").status_code == 404
    assert (
        client.get("/api/v1/hypotheses/h_missing/events").status_code == 404
    )
