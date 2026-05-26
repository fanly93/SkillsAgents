import json
from pathlib import Path

from fastapi.testclient import TestClient


def test_mock_quickstart_flow_creates_tenant_scoped_artifacts(tmp_path):
    from skills_agents.api.app import create_app

    client = TestClient(
        create_app(
            tenant_config_path=Path("examples/config/tenants.yaml"),
            data_root=tmp_path,
        )
    )

    health = client.get("/v1/health")
    assert health.status_code == 200
    assert health.json()["providers"]["model"] == "mock"

    fashion_reload = client.post("/v1/skills/reload", json={"tenant_id": "fashion_store"})
    electronics_reload = client.post("/v1/skills/reload", json={"tenant_id": "electronics_store"})
    assert fashion_reload.status_code == 200
    assert electronics_reload.status_code == 200
    assert fashion_reload.json()["registered"] >= 1
    assert electronics_reload.json()["registered"] >= 1

    fashion_skills = client.get("/v1/skills", params={"tenant_id": "fashion_store"}).json()["skills"]
    electronics_skills = client.get("/v1/skills", params={"tenant_id": "electronics_store"}).json()["skills"]
    assert {skill["name"] for skill in fashion_skills} == {"fashion-return-policy"}
    assert {skill["name"] for skill in electronics_skills} == {"electronics-return-policy"}

    fashion_session = client.post(
        "/v1/sessions",
        json={"tenant_id": "fashion_store", "user_id": "user_demo"},
    ).json()
    electronics_session = client.post(
        "/v1/sessions",
        json={"tenant_id": "electronics_store", "user_id": "user_demo"},
    ).json()

    fashion_chat = client.post(
        "/v1/chat",
        json={
            "tenant_id": "fashion_store",
            "user_id": "user_demo",
            "session_id": fashion_session["session_id"],
            "message": "I want to return a jacket. What should I do?",
        },
    )
    electronics_chat = client.post(
        "/v1/chat",
        json={
            "tenant_id": "electronics_store",
            "user_id": "user_demo",
            "session_id": electronics_session["session_id"],
            "message": "I want to return headphones. What should I do?",
        },
    )

    assert fashion_chat.status_code == 200
    assert electronics_chat.status_code == 200
    fashion_body = fashion_chat.json()
    electronics_body = electronics_chat.json()
    assert fashion_body["activated_skills"][0]["name"] == "fashion-return-policy"
    assert electronics_body["activated_skills"][0]["name"] == "electronics-return-policy"
    assert "fashion" in fashion_body["reply"].lower()
    assert "electronics" in electronics_body["reply"].lower()
    assert fashion_body["sources"][0]["source_id"].startswith("fashion_store:")
    assert electronics_body["sources"][0]["source_id"].startswith("electronics_store:")
    assert fashion_body["handoff_required"] is False
    fashion_session_state = json.loads(
        (tmp_path / "tenants" / "fashion_store" / "sessions" / f"{fashion_session['session_id']}.json").read_text(
            encoding="utf-8"
        )
    )
    assert fashion_session_state["active_skills"][0]["resource_manifest"]
    assert "Fashion Return Policy" in fashion_session_state["active_skills"][0]["instructions"]

    task_response = client.get(
        f"/v1/tasks/{fashion_session['session_id']}",
        params={"tenant_id": "fashion_store"},
    )
    assert task_response.status_code == 200
    assert "Answer customer question" in task_response.json()["markdown"]

    high_risk_chat = client.post(
        "/v1/chat",
        json={
            "tenant_id": "fashion_store",
            "user_id": "user_demo",
            "session_id": fashion_session["session_id"],
            "message": "Please directly refund my order and change my delivery address.",
        },
    )
    assert high_risk_chat.status_code == 200
    high_risk_body = high_risk_chat.json()
    assert high_risk_body["handoff_required"] is True
    assert high_risk_body["requires_human_approval"] is True
    assert high_risk_body["handoff_payload_path"]

    fashion_root = tmp_path / "tenants" / "fashion_store"
    electronics_root = tmp_path / "tenants" / "electronics_store"
    assert (fashion_root / "sessions" / f"{fashion_session['session_id']}.json").exists()
    assert (fashion_root / "tasks" / f"{fashion_session['session_id']}.md").exists()
    assert (fashion_root / "memory" / "user_demo.json").exists()
    assert (fashion_root / "handoff" / f"{fashion_session['session_id']}.json").exists()
    assert not (electronics_root / "handoff" / f"{fashion_session['session_id']}.json").exists()

    handoff_payload = json.loads((fashion_root / "handoff" / f"{fashion_session['session_id']}.json").read_text())
    assert handoff_payload["tenant_id"] == "fashion_store"
    assert {"refund", "address_change"}.issubset(set(handoff_payload["risk_tags"]))
    assert handoff_payload["activated_skills"][0]["name"] == "fashion-return-policy"
    assert handoff_payload["sources"][0]["source_id"] == "fashion_store:returns"

    audit_events = [
        json.loads(line)
        for line in (fashion_root / "audit" / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    event_types = {event["event_type"] for event in audit_events}
    assert {
        "session_created",
        "task_updated",
        "chat_turn",
        "skill_activation",
        "retrieval",
        "memory_access",
        "guardrail_decision",
        "handoff_payload_created",
    }.issubset(event_types)
    assert all(event["tenant_id"] == "fashion_store" for event in audit_events)


def test_chat_rejects_session_user_mismatch_and_supports_skill_id(tmp_path):
    from skills_agents.api.app import create_app

    client = TestClient(
        create_app(
            tenant_config_path=Path("examples/config/tenants.yaml"),
            data_root=tmp_path,
        )
    )
    skill_id = client.get("/v1/skills", params={"tenant_id": "fashion_store"}).json()["skills"][0]["skill_id"]
    session = client.post(
        "/v1/sessions",
        json={"tenant_id": "fashion_store", "user_id": "user_demo"},
    ).json()

    by_id = client.post(
        "/v1/chat",
        json={
            "tenant_id": "fashion_store",
            "user_id": "user_demo",
            "session_id": session["session_id"],
            "skill_id": skill_id,
            "message": "Please handle this manually.",
        },
    )
    mismatch = client.post(
        "/v1/chat",
        json={
            "tenant_id": "fashion_store",
            "user_id": "other_user",
            "session_id": session["session_id"],
            "message": "Can I use this session?",
        },
    )
    cross_tenant_id = client.post(
        "/v1/chat",
        json={
            "tenant_id": "fashion_store",
            "user_id": "user_demo",
            "session_id": session["session_id"],
            "skill_id": "electronics_store:electronics-return-policy",
            "message": "Use this skill for return policy.",
        },
    )

    assert by_id.status_code == 200
    assert by_id.json()["activated_skills"][0]["skill_id"] == skill_id
    assert by_id.json()["activated_skills"][0]["selection_reason"] == "explicit"
    assert mismatch.status_code == 403
    assert mismatch.json()["error"] == "session_user_mismatch"
    assert cross_tenant_id.status_code == 400
    assert cross_tenant_id.json()["error"] == "skill_not_enabled"
