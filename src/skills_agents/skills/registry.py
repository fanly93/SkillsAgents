from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .parser import ParsedSkill, SkillParser


@dataclass(frozen=True)
class SkillEntry:
    tenant_id: str
    skill_id: str
    name: str
    description: str
    version: str | None
    source: str
    root_path: Path
    checksum: str
    enabled: bool = True
    metadata: dict = field(default_factory=dict)
    body: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RefreshResult:
    scanned: int
    registered: int
    warnings: list[str]


class SkillRegistry:
    def __init__(self, parser: SkillParser | None = None):
        self._parser = parser or SkillParser()
        self._entries: dict[str, dict[str, SkillEntry]] = {}

    def refresh(self, tenant_id: str, source_paths: list[str | Path]) -> RefreshResult:
        tenant_entries: dict[str, SkillEntry] = {}
        warnings: list[str] = []
        scanned = 0

        for source in source_paths:
            source_path = Path(source)
            if not source_path.exists():
                warnings.append(f"Skill source does not exist: {source_path}")
                continue
            source_root = source_path.resolve()
            for skill_root in sorted(path for path in source_path.iterdir() if path.is_dir()):
                resolved_skill_root = skill_root.resolve()
                if source_root != resolved_skill_root and source_root not in resolved_skill_root.parents:
                    warnings.append(f"Skill root escapes skill source: {skill_root}")
                    continue
                if not (skill_root / "SKILL.md").exists():
                    continue
                scanned += 1
                try:
                    parsed = self._parser.parse_manifest(skill_root)
                    if parsed.name in tenant_entries:
                        warnings.append(f"Duplicate skill name for tenant {tenant_id}: {parsed.name}")
                        continue
                    tenant_entries[parsed.name] = self._entry_from_parsed(tenant_id, source_path, parsed)
                except ValueError as exc:
                    warnings.append(str(exc))

        self._entries[tenant_id] = tenant_entries
        return RefreshResult(scanned=scanned, registered=len(tenant_entries), warnings=warnings)

    def list(self, tenant_id: str) -> list[SkillEntry]:
        return list(self._entries.get(tenant_id, {}).values())

    def get_by_name(self, tenant_id: str, skill_name: str) -> SkillEntry | None:
        return self._entries.get(tenant_id, {}).get(skill_name)

    def get_by_id(self, tenant_id: str, skill_id: str) -> SkillEntry | None:
        for entry in self.list(tenant_id):
            if entry.skill_id == skill_id:
                return entry
        return None

    def _entry_from_parsed(self, tenant_id: str, source_path: Path, parsed: ParsedSkill) -> SkillEntry:
        return SkillEntry(
            tenant_id=tenant_id,
            skill_id=f"{tenant_id}:{parsed.name}",
            name=parsed.name,
            description=parsed.description,
            version=parsed.version,
            source=str(source_path),
            root_path=parsed.root_path,
            checksum=parsed.checksum,
            metadata=parsed.metadata,
            body=parsed.body,
            warnings=parsed.warnings,
        )
