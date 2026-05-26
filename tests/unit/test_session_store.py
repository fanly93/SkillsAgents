from skills_agents.core.context import TenantContext


def test_session_store_saves_appends_loads_and_recovers_corrupt_json(tmp_path):
    from skills_agents.memory.short_term import ShortTermMemoryStore
    from skills_agents.storage.paths import TenantPathResolver

    context = TenantContext(
        tenant_id="fashion_store",
        user_id="user_demo",
        session_id="sess_001",
    )
    store = ShortTermMemoryStore(TenantPathResolver(tmp_path))

    store.save(
        context,
        {
            "summary": "Initial summary",
            "messages": [],
            "active_skills": [],
            "recent_sources": [],
            "risk_tags": [],
            "handoff": {"required": False},
        },
    )
    store.append_message(context, {"role": "user", "content": "Can I return this?"})

    loaded = store.load(context)
    assert loaded["tenant_id"] == "fashion_store"
    assert loaded["user_id"] == "user_demo"
    assert loaded["session_id"] == "sess_001"
    assert loaded["messages"] == [{"role": "user", "content": "Can I return this?"}]

    path = store.path_for(context)
    path.write_text("{broken", encoding="utf-8")

    recovered = store.load(context)
    assert recovered["tenant_id"] == "fashion_store"
    assert recovered["messages"] == []
    assert list(path.parent.glob("sess_001.json.corrupt-*"))
