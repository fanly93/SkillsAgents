from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .registry import SkillRegistry


@dataclass(frozen=True)
class SkillActivation:
    tenant_id: str
    skill_id: str
    name: str
    version: str | None
    checksum: str
    instructions: str
    resource_manifest: dict[str, list[str]]


class SkillActivationService:
    def __init__(self, registry: SkillRegistry):
        self._registry = registry

    def activate(self, tenant_id: str, skill_id: str) -> SkillActivation:
        entry = self._registry.get_by_id(tenant_id, skill_id)
        if not entry:
            raise ValueError(f"Skill is not enabled for tenant {tenant_id}: {skill_id}")
        return SkillActivation(
            tenant_id=tenant_id,
            skill_id=entry.skill_id,
            name=entry.name,
            version=entry.version,
            checksum=entry.checksum,
            instructions=entry.body,
            resource_manifest=_resource_manifest(entry.root_path),
        )


def _resource_manifest(root: Path) -> dict[str, list[str]]:
    manifest: dict[str, list[str]] = {"references": [], "assets": [], "scripts": []}
    for folder in manifest:
        base = root / folder
        if not base.exists():
            continue
        manifest[folder] = [
            str(path.relative_to(root))
            for path in sorted(base.rglob("*"))
            if path.is_file()
        ]
    return manifest
