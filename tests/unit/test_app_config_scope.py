from pathlib import Path

import yaml
from fastapi.testclient import TestClient


def test_app_filters_cross_tenant_skill_and_knowledge_paths(tmp_path):
    from skills_agents.api.app import create_app

    fashion_skill = tmp_path / "examples" / "skills" / "tenants" / "fashion_store" / "fashion-skill"
    electronics_skill = tmp_path / "examples" / "skills" / "tenants" / "electronics_store" / "electronics-skill"
    fashion_knowledge = tmp_path / "examples" / "data" / "tenants" / "fashion_store" / "knowledge"
    electronics_knowledge = tmp_path / "examples" / "data" / "tenants" / "electronics_store" / "knowledge"
    fashion_skill.mkdir(parents=True)
    electronics_skill.mkdir(parents=True)
    fashion_knowledge.mkdir(parents=True)
    electronics_knowledge.mkdir(parents=True)
    (fashion_skill / "SKILL.md").write_text(
        "---\nname: fashion-skill\ndescription: Fashion returns.\n---\nFashion skill",
        encoding="utf-8",
    )
    (electronics_skill / "SKILL.md").write_text(
        "---\nname: electronics-skill\ndescription: Electronics returns.\n---\nElectronics skill",
        encoding="utf-8",
    )
    (electronics_knowledge / "returns.md").write_text(
        "# Electronics Secret\nElectronics return policy.",
        encoding="utf-8",
    )
    config_path = tmp_path / "tenants.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "tenants": {
                    "fashion_store": {
                        "skill_sources": [
                            str(fashion_skill.parent),
                            str(electronics_skill.parent),
                        ],
                        "knowledge_paths": [
                            str(fashion_knowledge),
                            str(electronics_knowledge),
                        ],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    client = TestClient(create_app(tenant_config_path=config_path, data_root=tmp_path / "data"))

    skills = client.get("/v1/skills", params={"tenant_id": "fashion_store"}).json()["skills"]
    session = client.post(
        "/v1/sessions",
        json={"tenant_id": "fashion_store", "user_id": "user_demo"},
    ).json()
    chat = client.post(
        "/v1/chat",
        json={
            "tenant_id": "fashion_store",
            "user_id": "user_demo",
            "session_id": session["session_id"],
            "message": "electronics return policy",
        },
    ).json()

    assert {skill["name"] for skill in skills} == {"fashion-skill"}
    assert chat["sources"] == []
