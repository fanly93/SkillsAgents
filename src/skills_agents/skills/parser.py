from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ParsedSkill:
    name: str
    description: str
    version: str | None
    metadata: dict[str, Any]
    body: str
    root_path: Path
    checksum: str
    warnings: list[str] = field(default_factory=list)


class SkillParser:
    def parse_manifest(self, skill_root: str | Path) -> ParsedSkill:
        root = Path(skill_root)
        manifest = root / "SKILL.md"
        if not manifest.exists():
            raise ValueError(f"Missing SKILL.md in {root}")

        raw = manifest.read_text(encoding="utf-8")
        frontmatter, body = self._split_frontmatter(raw)
        name = str(frontmatter.get("name") or "").strip()
        description = str(frontmatter.get("description") or "").strip()
        warnings: list[str] = []
        if not name:
            raise ValueError(f"Skill at {root} is missing name")
        if not description:
            raise ValueError(f"Skill {name} is missing description")
        if (root / "asserts").exists() and not (root / "assets").exists():
            warnings.append("Found non-standard asserts/ directory; use assets/ instead")

        return ParsedSkill(
            name=name,
            description=description,
            version=frontmatter.get("version"),
            metadata=frontmatter.get("metadata") or {},
            body=body.strip(),
            root_path=root,
            checksum=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            warnings=warnings,
        )

    def _split_frontmatter(self, raw: str) -> tuple[dict[str, Any], str]:
        if not raw.startswith("---"):
            return {}, raw
        parts = raw.split("---", 2)
        if len(parts) < 3:
            return {}, raw
        data = yaml.safe_load(parts[1]) or {}
        if not isinstance(data, dict):
            data = {}
        return data, parts[2]
