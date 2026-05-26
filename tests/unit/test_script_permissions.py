import json

from skills_agents.core.context import TenantContext


def test_permission_policy_denies_scripts_by_default_and_blocks_path_escape(tmp_path):
    from skills_agents.scripts.permissions import PermissionPolicy

    context = TenantContext(
        tenant_id="fashion_store",
        user_id="user_demo",
        session_id="sess_001",
    )
    skill_root = tmp_path / "skill"
    script = skill_root / "scripts" / "refund.py"
    outside = tmp_path / "outside.py"
    script.parent.mkdir(parents=True)
    script.write_text("print('refund')", encoding="utf-8")
    outside.write_text("print('outside')", encoding="utf-8")

    policy = PermissionPolicy()

    default_decision = policy.authorize(context, skill_root=skill_root, script_path=script, input_data={})
    escape_decision = policy.authorize(context, skill_root=skill_root, script_path=outside, input_data={})

    assert default_decision["allowed"] is False
    assert default_decision["reason"] == "script_execution_denied_by_default"
    assert default_decision["tenant_id"] == "fashion_store"
    assert escape_decision["allowed"] is False
    assert escape_decision["reason"] == "script_path_outside_skill_root"


def test_script_executor_never_runs_denied_script_and_audits_decision(tmp_path):
    from skills_agents.audit.jsonl import JsonlAuditSink
    from skills_agents.scripts.executor import ScriptExecutor
    from skills_agents.scripts.permissions import PermissionPolicy
    from skills_agents.storage.paths import TenantPathResolver

    context = TenantContext(
        tenant_id="fashion_store",
        user_id="user_demo",
        session_id="sess_001",
    )
    skill_root = tmp_path / "skill"
    script = skill_root / "scripts" / "refund.py"
    marker = tmp_path / "executed.txt"
    script.parent.mkdir(parents=True)
    script.write_text(f"{marker}.write_text('executed')", encoding="utf-8")
    paths = TenantPathResolver(tmp_path / "data")
    executor = ScriptExecutor(
        permission_policy=PermissionPolicy(),
        audit_sink=JsonlAuditSink(paths),
    )

    result = executor.execute(
        context,
        skill_root=skill_root,
        script_path=script,
        input_data={"order_id": "order_001"},
    )

    assert result["status"] == "denied"
    assert marker.exists() is False
    events = [
        json.loads(line)
        for line in paths.audit_path("fashion_store").read_text(encoding="utf-8").splitlines()
    ]
    assert events[0]["event_type"] == "script_authorization_decision"
    assert events[0]["decision"]["allowed"] is False
