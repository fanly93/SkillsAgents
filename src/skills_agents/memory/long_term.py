from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from skills_agents.core.context import TenantContext
from skills_agents.storage.atomic import read_json, write_json
from skills_agents.storage.paths import TenantPathResolver


class JsonLongTermMemoryProvider:
    def __init__(self, paths: TenantPathResolver):
        self._paths = paths

    def path_for(self, context: TenantContext) -> Path:
        if not context.user_id:
            raise ValueError("user_id is required")
        return self._paths.memory_path(context.tenant_id, context.user_id)

    def add(
        self,
        context: TenantContext,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state = self._load_state(context)
        record = {
            "memory_id": f"mem_{uuid4().hex[:12]}",
            "tenant_id": context.tenant_id,
            "user_id": context.user_id,
            "content": content,
            "metadata": metadata or {},
            "created_at": _now(),
        }
        state["memories"].append(record)
        write_json(self.path_for(context), state)
        return record

    def search(self, context: TenantContext, query: str, limit: int = 5) -> list[dict[str, Any]]:
        terms = _terms(query)
        scored: list[tuple[int, dict[str, Any]]] = []
        for record in self._load_state(context)["memories"]:
            score = len(terms & _terms(record.get("content", "")))
            if score:
                scored.append((score, record))
        scored.sort(key=lambda item: (-item[0], item[1]["created_at"]))
        return [record for _, record in scored[:limit]]

    def _load_state(self, context: TenantContext) -> dict[str, Any]:
        return read_json(
            self.path_for(context),
            default={
                "tenant_id": context.tenant_id,
                "user_id": context.user_id,
                "memories": [],
            },
        )


def _terms(text: str) -> set[str]:
    return {term.lower() for term in text.split() if len(term) > 2}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
