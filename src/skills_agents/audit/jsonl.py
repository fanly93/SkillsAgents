from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from skills_agents.core.context import TenantContext
from skills_agents.storage.atomic import append_jsonl
from skills_agents.storage.paths import TenantPathResolver


class JsonlAuditSink:
    def __init__(self, paths: TenantPathResolver):
        self.paths = paths

    def write(self, context: TenantContext, event: dict[str, Any]) -> None:
        payload = {
            "timestamp": _now(),
            "tenant_id": context.tenant_id,
            "user_id": context.user_id,
            "session_id": context.session_id,
            **event,
        }
        append_jsonl(self.paths.audit_path(context.tenant_id), payload)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
