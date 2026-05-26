from skills_agents.core.context import TenantContext


def test_rule_guardrail_requires_handoff_for_high_risk_business_actions():
    from skills_agents.safety.guardrails import RuleBasedGuardrailProvider

    guardrail = RuleBasedGuardrailProvider()
    context = TenantContext(
        tenant_id="fashion_store",
        user_id="user_demo",
        session_id="sess_001",
    )

    decision = guardrail.evaluate(context, "Please refund this order and change my delivery address.")

    assert decision["tenant_id"] == "fashion_store"
    assert decision["session_id"] == "sess_001"
    assert decision["risk_level"] == "high"
    assert decision["decision"] == "handoff_required"
    assert decision["handoff_required"] is True
    assert "refund" in decision["risk_tags"]
    assert "address_change" in decision["risk_tags"]
    assert "human review" in decision["reason"].lower()


def test_rule_guardrail_allows_safe_policy_questions_and_redacts_pii():
    from skills_agents.safety.guardrails import RuleBasedGuardrailProvider

    guardrail = RuleBasedGuardrailProvider()
    context = TenantContext(
        tenant_id="fashion_store",
        user_id="user_demo",
        session_id="sess_001",
    )

    decision = guardrail.evaluate(context, "What is your return policy? My phone is 555-123-4567.")

    assert decision["risk_level"] == "low"
    assert decision["decision"] == "allow"
    assert decision["handoff_required"] is False
    assert "pii_phone" in decision["risk_tags"]
    assert decision["redactions"]["message"] == "What is your return policy? My phone is [REDACTED_PHONE]."
