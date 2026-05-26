from pathlib import Path

import yaml


def test_sample_tenants_register_isolated_skills():
    from skills_agents.skills.registry import SkillRegistry

    config = yaml.safe_load(Path("examples/config/tenants.yaml").read_text(encoding="utf-8"))
    registry = SkillRegistry()

    for tenant_id, tenant in config["tenants"].items():
        registry.refresh(tenant_id, [Path(path) for path in tenant["skill_sources"]])

    fashion_names = {skill.name for skill in registry.list("fashion_store")}
    electronics_names = {skill.name for skill in registry.list("electronics_store")}

    assert "fashion-return-policy" in fashion_names
    assert "electronics-return-policy" in electronics_names
    assert "electronics-return-policy" not in fashion_names
    assert "fashion-return-policy" not in electronics_names


def test_sample_tenants_keyword_select_different_skills():
    from skills_agents.skills.registry import SkillRegistry
    from skills_agents.skills.selector import KeywordSelector

    config = yaml.safe_load(Path("examples/config/tenants.yaml").read_text(encoding="utf-8"))
    registry = SkillRegistry()
    for tenant_id, tenant in config["tenants"].items():
        registry.refresh(tenant_id, [Path(path) for path in tenant["skill_sources"]])

    selector = KeywordSelector(registry)
    fashion = selector.select("fashion_store", "I want to return a jacket")
    electronics = selector.select("electronics_store", "I want to return headphones")

    assert fashion.name == "fashion-return-policy"
    assert electronics.name == "electronics-return-policy"
