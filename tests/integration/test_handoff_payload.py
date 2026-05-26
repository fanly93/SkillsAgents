import json

from skills_agents.core.context import TenantContext


def test_handoff_payload_and_audit_events_are_tenant_scoped(tmp_path):
    from skills_agents.audit.jsonl import JsonlAuditSink
    from skills_agents.handoff.service import HandoffService
    from skills_agents.safety.guardrails import RuleBasedGuardrailProvider
    from skills_agents.storage.paths import TenantPathResolver

    paths = TenantPathResolver(tmp_path)
    context = TenantContext(
        tenant_id="fashion_store",
        user_id="user_demo",
        session_id="sess_001",
    )
    session_state = {
        "summary": "Customer asks about a return, then requests a refund.",
        "messages": [
            {"role": "user", "content": "Can I return this jacket?"},
            {"role": "assistant", "content": "I can explain the policy."},
            {"role": "user", "content": "Please refund the order now."},
        ],
        "active_skills": [{"skill_id": "fashion-return-policy", "name": "fashion-return-policy"}],
    }
    task_summary = {"total": 2, "completed": 1, "failed": 0, "pending": 1}
    sources = [{"source_id": "return-policy", "title": "Return Policy", "snippet": "Returns are reviewed."}]

    guardrail = RuleBasedGuardrailProvider()
    audit = JsonlAuditSink(paths)
    handoff = HandoffService(paths, audit_sink=audit)

    decision = guardrail.evaluate(context, "Please refund the order now.")
    audit.write(context, {"event_type": "guardrail_decision", "decision": decision})
    payload_path = handoff.create_payload(
        context=context,
        session_state=session_state,
        task_summary=task_summary,
        sources=sources,
        guardrail_decision=decision,
    )

    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    assert payload_path == paths.handoff_path("fashion_store", "sess_001")
    assert payload["tenant_id"] == "fashion_store"
    assert payload["user_id"] == "user_demo"
    assert payload["session_id"] == "sess_001"
    assert payload["status"] == "review_pending"
    assert payload["risk_tags"] == ["refund"]
    assert payload["session_summary"] == session_state["summary"]
    assert payload["messages_or_summary"] == session_state["messages"]
    assert payload["activated_skills"] == session_state["active_skills"]
    assert payload["task_status"] == task_summary
    assert payload["sources"] == sources
    assert payload["agent_attempted_steps"] == []
    assert payload["recommended_next_steps"]

    audit_lines = paths.audit_path("fashion_store").read_text(encoding="utf-8").splitlines()
    events = [json.loads(line) for line in audit_lines]
    assert [event["event_type"] for event in events] == [
        "guardrail_decision",
        "handoff_payload_created",
    ]
    assert all(event["tenant_id"] == "fashion_store" for event in events)

    other_context = TenantContext(
        tenant_id="electronics_store",
        user_id="user_demo",
        session_id="sess_001",
    )
    other_payload = handoff.path_for(other_context)
    assert not other_payload.exists()
    assert not paths.audit_path("electronics_store").exists()
