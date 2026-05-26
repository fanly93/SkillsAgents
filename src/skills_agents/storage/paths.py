import re
from pathlib import Path


_SAFE_TENANT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


class TenantPathResolver:
    def __init__(self, data_root: str | Path):
        self.data_root = Path(data_root)

    def tenant_root(self, tenant_id: str) -> Path:
        if not _SAFE_TENANT_ID.fullmatch(tenant_id):
            raise ValueError("tenant_id contains unsafe path characters")
        tenants_root = (self.data_root / "tenants").resolve()
        root = (tenants_root / tenant_id).resolve()
        if tenants_root != root and tenants_root not in root.parents:
            raise ValueError("Resolved tenant path escapes tenants directory")
        return root

    def artifact_path(self, tenant_id: str, category: str, name: str) -> Path:
        root = (self.tenant_root(tenant_id) / category).resolve()
        path = (root / name).resolve()
        if root != path and root not in path.parents:
            raise ValueError("Resolved path escapes tenant artifact directory")
        return path

    def session_path(self, tenant_id: str, session_id: str) -> Path:
        return self.artifact_path(tenant_id, "sessions", f"{session_id}.json")

    def task_path(self, tenant_id: str, session_id: str) -> Path:
        return self.artifact_path(tenant_id, "tasks", f"{session_id}.md")

    def memory_path(self, tenant_id: str, user_id: str) -> Path:
        return self.artifact_path(tenant_id, "memory", f"{user_id}.json")

    def audit_path(self, tenant_id: str) -> Path:
        return self.artifact_path(tenant_id, "audit", "events.jsonl")

    def handoff_path(self, tenant_id: str, session_id: str) -> Path:
        return self.artifact_path(tenant_id, "handoff", f"{session_id}.json")
