from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from skills_agents.core.context import TenantContext
from skills_agents.storage.atomic import read_json, write_json
from skills_agents.storage.paths import TenantPathResolver


class ShortTermMemoryStore:
    def __init__(self, paths: TenantPathResolver):
        self._paths = paths

    def path_for(self, context: TenantContext) -> Path:
        if not context.session_id:
            raise ValueError("session_id is required")
        return self._paths.session_path(context.tenant_id, context.session_id)

    def load(self, context: TenantContext) -> dict[str, Any]:
        state = read_json(self.path_for(context), default=None)
        if state is None:
            return self._empty_state(context)
        return state

    def save(self, context: TenantContext, state: dict[str, Any]) -> None:
        now = _now()
        existing = read_json(self.path_for(context), default={}) or {}
        created_at = existing.get("created_at") or now
        normalized = {
            "tenant_id": context.tenant_id,
            "user_id": context.user_id,
            "session_id": context.session_id,
            "created_at": created_at,
            "updated_at": now,
            "messages": state.get("messages", []),
            "summary": state.get("summary", ""),
            "active_skills": state.get("active_skills", []),
            "recent_sources": state.get("recent_sources", []),
            "risk_tags": state.get("risk_tags", []),
            "handoff": state.get("handoff", {"required": False}),
        }
        write_json(self.path_for(context), normalized)

    def append_message(self, context: TenantContext, message: dict[str, Any]) -> None:
        state = self.load(context)
        state.setdefault("messages", []).append(message)
        self.save(context, state)

    def _empty_state(self, context: TenantContext) -> dict[str, Any]:
        now = _now()
        return {
            "tenant_id": context.tenant_id,
            "user_id": context.user_id,
            "session_id": context.session_id,
            "created_at": now,
            "updated_at": now,
            "messages": [],
            "summary": "",
            "active_skills": [],
            "recent_sources": [],
            "risk_tags": [],
            "handoff": {"required": False},
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
