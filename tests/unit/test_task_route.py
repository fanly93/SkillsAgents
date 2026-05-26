from fastapi import FastAPI
from fastapi.testclient import TestClient

from skills_agents.core.context import TenantContext


def test_task_route_returns_tenant_scoped_markdown(tmp_path):
    from skills_agents.api.routes import create_task_router
    from skills_agents.storage.paths import TenantPathResolver
    from skills_agents.tasks.tracker import TaskTracker

    tracker = TaskTracker(TenantPathResolver(tmp_path))
    context = TenantContext(
        tenant_id="fashion_store",
        user_id="user_demo",
        session_id="sess_001",
    )
    tracker.create_plan(
        context,
        goal="Answer return policy question",
        tasks=[{"task_id": "T001", "description": "Identify return intent"}],
    )

    app = FastAPI()
    app.include_router(create_task_router(tracker))
    client = TestClient(app)

    response = client.get("/v1/tasks/sess_001", params={"tenant_id": "fashion_store"})

    assert response.status_code == 200
    assert response.json()["tenant_id"] == "fashion_store"
    assert "- [ ] T001 Identify return intent" in response.json()["markdown"]
    assert response.json()["summary"] == {"total": 1, "completed": 0, "failed": 0, "pending": 1}


def test_task_route_returns_404_for_wrong_tenant(tmp_path):
    from skills_agents.api.routes import create_task_router
    from skills_agents.storage.paths import TenantPathResolver
    from skills_agents.tasks.tracker import TaskTracker

    tracker = TaskTracker(TenantPathResolver(tmp_path))
    context = TenantContext(
        tenant_id="fashion_store",
        user_id="user_demo",
        session_id="sess_001",
    )
    tracker.create_plan(
        context,
        goal="Answer return policy question",
        tasks=[{"task_id": "T001", "description": "Identify return intent"}],
    )

    app = FastAPI()
    app.include_router(create_task_router(tracker))
    client = TestClient(app)

    response = client.get("/v1/tasks/sess_001", params={"tenant_id": "electronics_store"})

    assert response.status_code == 404
    assert response.json()["error"] == "task_not_found"


def test_task_route_returns_404_for_unknown_tenant_when_known_tenants_provided(tmp_path):
    from skills_agents.api.routes import create_task_router
    from skills_agents.storage.paths import TenantPathResolver
    from skills_agents.tasks.tracker import TaskTracker

    app = FastAPI()
    app.include_router(
        create_task_router(
            TaskTracker(TenantPathResolver(tmp_path)),
            tenant_ids={"fashion_store"},
        )
    )
    client = TestClient(app)

    response = client.get("/v1/tasks/sess_001", params={"tenant_id": "unknown_store"})

    assert response.status_code == 404
    assert response.json()["error"] == "unknown_tenant"


def test_task_route_rejects_unsafe_tenant_ids(tmp_path):
    from skills_agents.api.routes import create_task_router
    from skills_agents.storage.paths import TenantPathResolver
    from skills_agents.tasks.tracker import TaskTracker

    app = FastAPI()
    app.include_router(create_task_router(TaskTracker(TenantPathResolver(tmp_path))))
    client = TestClient(app)

    response = client.get("/v1/tasks/sess_001", params={"tenant_id": "../escape"})

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_tenant_id"
