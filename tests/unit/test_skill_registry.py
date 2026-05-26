from pathlib import Path

import pytest


VALID_SKILL = """---
name: return-policy
description: Use when answering return policy questions.
version: 1.0.0
metadata:
  tags:
    - return
    - policy
---

# Return Policy

Follow the tenant return policy and cite sources when available.
"""


def test_parser_reads_frontmatter_body_and_checksum(tmp_path):
    from skills_agents.skills.parser import SkillParser

    skill_root = tmp_path / "return-policy"
    skill_root.mkdir()
    (skill_root / "SKILL.md").write_text(VALID_SKILL, encoding="utf-8")

    parsed = SkillParser().parse_manifest(skill_root)

    assert parsed.name == "return-policy"
    assert parsed.description == "Use when answering return policy questions."
    assert parsed.version == "1.0.0"
    assert parsed.body.startswith("# Return Policy")
    assert parsed.checksum
    assert parsed.warnings == []


def test_registry_registers_valid_skills_and_warns_invalid(tmp_path):
    from skills_agents.skills.registry import SkillRegistry

    valid_root = tmp_path / "valid" / "return-policy"
    invalid_root = tmp_path / "invalid" / "broken-skill"
    valid_root.mkdir(parents=True)
    invalid_root.mkdir(parents=True)
    (valid_root / "SKILL.md").write_text(VALID_SKILL, encoding="utf-8")
    (invalid_root / "SKILL.md").write_text("---\nname: broken-skill\n---\nMissing description", encoding="utf-8")

    registry = SkillRegistry()
    result = registry.refresh(
        tenant_id="fashion_store",
        source_paths=[tmp_path / "valid", tmp_path / "invalid"],
    )

    skills = registry.list("fashion_store")
    assert result.scanned == 2
    assert result.registered == 1
    assert skills[0].name == "return-policy"
    assert result.warnings


def test_registry_ignores_symlinked_skill_root_that_escapes_source(tmp_path):
    from skills_agents.skills.registry import SkillRegistry

    source = tmp_path / "source"
    outside_skill = tmp_path / "outside" / "return-policy"
    source.mkdir()
    outside_skill.mkdir(parents=True)
    (outside_skill / "SKILL.md").write_text(VALID_SKILL, encoding="utf-8")
    (source / "return-policy").symlink_to(outside_skill, target_is_directory=True)

    registry = SkillRegistry()
    result = registry.refresh("fashion_store", [source])

    assert registry.list("fashion_store") == []
    assert result.registered == 0
    assert any("escapes skill source" in warning for warning in result.warnings)


def test_keyword_selector_matches_description_and_explicit_selection_wins(tmp_path):
    from skills_agents.skills.registry import SkillRegistry
    from skills_agents.skills.selector import ExplicitSelector, KeywordSelector

    skill_root = tmp_path / "skills" / "return-policy"
    skill_root.mkdir(parents=True)
    (skill_root / "SKILL.md").write_text(VALID_SKILL, encoding="utf-8")
    registry = SkillRegistry()
    registry.refresh("fashion_store", [tmp_path / "skills"])

    explicit = ExplicitSelector(registry).select(
        tenant_id="fashion_store",
        message="shipping question",
        skill_name="return-policy",
    )
    keyword = KeywordSelector(registry).select(
        tenant_id="fashion_store",
        message="Can I return this product?",
    )

    assert explicit and explicit.selection_reason == "explicit"
    assert keyword and keyword.selection_reason == "keyword"
    with pytest.raises(ValueError):
        ExplicitSelector(registry).select(
            tenant_id="electronics_store",
            message="return",
            skill_name="return-policy",
        )


def test_activation_returns_instructions_manifest_and_checksum(tmp_path):
    from skills_agents.skills.activation import SkillActivationService
    from skills_agents.skills.registry import SkillRegistry
    from skills_agents.skills.selector import ExplicitSelector

    skill_root = tmp_path / "skills" / "return-policy"
    (skill_root / "references").mkdir(parents=True)
    (skill_root / "references" / "policy.md").write_text("Return within 30 days.", encoding="utf-8")
    (skill_root / "SKILL.md").write_text(VALID_SKILL, encoding="utf-8")
    registry = SkillRegistry()
    registry.refresh("fashion_store", [tmp_path / "skills"])
    selected = ExplicitSelector(registry).select("fashion_store", "return", "return-policy")

    activation = SkillActivationService(registry).activate("fashion_store", selected.skill_id)

    assert activation.instructions.startswith("# Return Policy")
    assert activation.checksum == selected.checksum
    assert activation.resource_manifest["references"] == ["references/policy.md"]


def test_resource_reader_blocks_paths_and_symlinks_outside_skill_root(tmp_path):
    from skills_agents.skills.resources import SkillResourceReader

    skill_root = tmp_path / "skills" / "return-policy"
    outside = tmp_path / "outside"
    (skill_root / "references").mkdir(parents=True)
    outside.mkdir()
    (skill_root / "references" / "policy.md").write_text("Return within 30 days.", encoding="utf-8")
    (outside / "secret.md").write_text("Other tenant secret.", encoding="utf-8")
    (skill_root / "references" / "secret.md").symlink_to(outside / "secret.md")

    reader = SkillResourceReader(skill_root)

    assert reader.read_text("references/policy.md") == "Return within 30 days."
    with pytest.raises(ValueError):
        reader.read_text("../outside/secret.md")
    with pytest.raises(ValueError):
        reader.read_text("references/secret.md")
