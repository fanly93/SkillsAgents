from __future__ import annotations

from dataclasses import dataclass

from .registry import SkillEntry, SkillRegistry


@dataclass(frozen=True)
class SelectedSkill:
    tenant_id: str
    skill_id: str
    name: str
    description: str
    version: str | None
    checksum: str
    selection_reason: str


class ExplicitSelector:
    def __init__(self, registry: SkillRegistry):
        self._registry = registry

    def select(self, tenant_id: str, message: str, skill_name: str | None = None) -> SelectedSkill | None:
        if not skill_name:
            return None
        entry = self._registry.get_by_name(tenant_id, skill_name)
        if not entry:
            raise ValueError(f"Skill is not enabled for tenant {tenant_id}: {skill_name}")
        return _selected(entry, "explicit")

    def select_by_id(self, tenant_id: str, skill_id: str | None = None) -> SelectedSkill | None:
        if not skill_id:
            return None
        entry = self._registry.get_by_id(tenant_id, skill_id)
        if not entry:
            raise ValueError(f"Skill is not enabled for tenant {tenant_id}: {skill_id}")
        return _selected(entry, "explicit")


class KeywordSelector:
    def __init__(self, registry: SkillRegistry):
        self._registry = registry

    def select(self, tenant_id: str, message: str, skill_name: str | None = None) -> SelectedSkill | None:
        words = {word.strip(".,!?;:").lower() for word in message.split()}
        best: SkillEntry | None = None
        best_score = 0
        for entry in self._registry.list(tenant_id):
            haystack = f"{entry.name} {entry.description} {' '.join(entry.metadata.get('tags', []))}".lower()
            score = sum(1 for word in words if word and word in haystack)
            if score > best_score:
                best = entry
                best_score = score
        if not best:
            return None
        return _selected(best, "keyword")


def _selected(entry: SkillEntry, reason: str) -> SelectedSkill:
    return SelectedSkill(
        tenant_id=entry.tenant_id,
        skill_id=entry.skill_id,
        name=entry.name,
        description=entry.description,
        version=entry.version,
        checksum=entry.checksum,
        selection_reason=reason,
    )
