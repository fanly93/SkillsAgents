from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(f".{target.name}.tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, target)


def read_json(path: str | Path, default: dict[str, Any] | None = None) -> dict[str, Any] | None:
    target = Path(path)
    if not target.exists():
        return default
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        corrupt = target.with_name(f"{target.name}.corrupt-{stamp}")
        os.replace(target, corrupt)
        return default


def append_jsonl(path: str | Path, event: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
    with target.open("a", encoding="utf-8") as handle:
        handle.write(f"{line}\n")
