from pathlib import Path

from fastapi.testclient import TestClient


def _session(client: TestClient) -> str:
    response = client.post(
        "/v1/sessions",
        json={"tenant_id": "fashion_store", "user_id": "user_demo"},
    )
    return response.json()["session_id"]


def test_user_requested_escalation_creates_handoff_payload(tmp_path):
    from skills_agents.api.app import create_app

    client = TestClient(create_app(tenant_config_path=Path("examples/config/tenants.yaml"), data_root=tmp_path))
    session_id = _session(client)

    response = client.post(
        "/v1/chat",
        json={
            "tenant_id": "fashion_store",
            "user_id": "user_demo",
            "session_id": session_id,
            "message": "Please transfer me to a human agent.",
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["handoff_required"] is True
    assert "user_escalation" in body["risk_tags"]
    assert (tmp_path / "tenants" / "fashion_store" / "handoff" / f"{session_id}.json").exists()


def test_low_confidence_without_skill_or_sources_creates_handoff_payload(tmp_path):
    from skills_agents.api.app import create_app

    client = TestClient(create_app(tenant_config_path=Path("examples/config/tenants.yaml"), data_root=tmp_path))
    session_id = _session(client)

    response = client.post(
        "/v1/chat",
        json={
            "tenant_id": "fashion_store",
            "user_id": "user_demo",
            "session_id": session_id,
            "message": "blorptastic quantum pineapple",
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["handoff_required"] is True
    assert "low_confidence" in body["risk_tags"]
    assert body["sources"] == []


def test_failed_tool_metadata_creates_handoff_payload(tmp_path):
    from skills_agents.api.app import create_app

    client = TestClient(create_app(tenant_config_path=Path("examples/config/tenants.yaml"), data_root=tmp_path))
    session_id = _session(client)

    response = client.post(
        "/v1/chat",
        json={
            "tenant_id": "fashion_store",
            "user_id": "user_demo",
            "session_id": session_id,
            "message": "I need help with a return.",
            "metadata": {"tool_failed": True},
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["handoff_required"] is True
    assert "failed_tool" in body["risk_tags"]
