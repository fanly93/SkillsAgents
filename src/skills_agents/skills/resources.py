from __future__ import annotations

from pathlib import Path


class SkillResourceReader:
    def __init__(self, skill_root: str | Path):
        self.skill_root = Path(skill_root).resolve()

    def read_text(self, relative_path: str) -> str:
        path = (self.skill_root / relative_path).resolve()
        if self.skill_root != path and self.skill_root not in path.parents:
            raise ValueError("Resource path escapes skill root")
        if path.is_symlink():
            raise ValueError("Symlink resources are not allowed")
        return path.read_text(encoding="utf-8")
