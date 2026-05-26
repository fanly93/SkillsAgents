from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError


def test_create_session_request_requires_tenant_and_user():
    from skills_agents.api.schemas import CreateSessionRequest

    request = CreateSessionRequest(tenant_id="fashion_store", user_id="user_demo")

    assert request.tenant_id == "fashion_store"
    assert request.user_id == "user_demo"
    with pytest.raises(ValidationError):
        CreateSessionRequest(tenant_id="fashion_store")


def test_tenant_context_requires_non_empty_ids():
    from skills_agents.core.context import TenantContext

    context = TenantContext(
        tenant_id="fashion_store",
        user_id="user_demo",
        session_id="sess_001",
    )

    assert context.tenant_id == "fashion_store"
    with pytest.raises(ValidationError):
        TenantContext(tenant_id="", user_id="user_demo", session_id="sess_001")


def test_tenant_paths_are_confined_to_tenant_root(tmp_path):
    from skills_agents.storage.paths import TenantPathResolver

    resolver = TenantPathResolver(data_root=tmp_path)
    session_path = resolver.session_path("fashion_store", "sess_001")

    assert session_path == tmp_path / "tenants" / "fashion_store" / "sessions" / "sess_001.json"
    with pytest.raises(ValueError):
        resolver.artifact_path("fashion_store", "sessions", "../escape.json")
    with pytest.raises(ValueError):
        resolver.task_path("../escape", "sess_001")


def test_atomic_json_helpers_roundtrip_and_backup_corrupt_files(tmp_path):
    from skills_agents.storage.atomic import append_jsonl, read_json, write_json

    target = tmp_path / "state.json"
    write_json(target, {"session_id": "sess_001"})

    assert read_json(target) == {"session_id": "sess_001"}

    target.write_text("{broken", encoding="utf-8")
    assert read_json(target, default={"recovered": True}) == {"recovered": True}
    assert list(tmp_path.glob("state.json.corrupt-*"))

    events = tmp_path / "events.jsonl"
    append_jsonl(events, {"event_type": "session.created"})
    assert events.read_text(encoding="utf-8").strip() == '{"event_type":"session.created"}'


def test_provider_protocols_are_runtime_checkable():
    from skills_agents.core.orchestrator import ModelProvider

    class FakeModelProvider:
        def invoke(self, messages, tools=None, config=None):
            return {"content": "ok"}

    assert isinstance(FakeModelProvider(), ModelProvider)


def test_sample_tenant_config_declares_two_tenants():
    config_path = Path("examples/config/tenants.yaml")

    assert config_path.exists()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert set(config["tenants"]) >= {"fashion_store", "electronics_store"}
    assert config["tenants"]["fashion_store"]["skill_sources"]
    assert config["tenants"]["electronics_store"]["knowledge_paths"]
