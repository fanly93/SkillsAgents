from __future__ import annotations

from pathlib import Path
from typing import Any

from skills_agents.core.context import TenantContext


class PermissionPolicy:
    def authorize(
        self,
        context: TenantContext,
        *,
        skill_root: str | Path,
        script_path: str | Path,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        root = Path(skill_root).resolve()
        script = Path(script_path).resolve()
        if root != script and root not in script.parents:
            reason = "script_path_outside_skill_root"
        else:
            reason = "script_execution_denied_by_default"
        return {
            "tenant_id": context.tenant_id,
            "user_id": context.user_id,
            "session_id": context.session_id,
            "script_path": str(script),
            "allowed": False,
            "reason": reason,
            "input_keys": sorted(input_data),
        }
