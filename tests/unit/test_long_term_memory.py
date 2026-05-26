from skills_agents.core.context import TenantContext


def test_json_long_term_memory_adds_and_searches_tenant_user_records(tmp_path):
    from skills_agents.memory.long_term import JsonLongTermMemoryProvider
    from skills_agents.storage.paths import TenantPathResolver

    provider = JsonLongTermMemoryProvider(TenantPathResolver(tmp_path))
    fashion = TenantContext(tenant_id="fashion_store", user_id="user_demo", session_id="sess_001")
    electronics = TenantContext(tenant_id="electronics_store", user_id="user_demo", session_id="sess_001")

    added = provider.add(fashion, "Customer asked about jacket returns.", {"session_id": "sess_001"})
    provider.add(electronics, "Customer asked about headphone returns.", {"session_id": "sess_001"})

    results = provider.search(fashion, "jacket returns")

    assert added["memory_id"]
    assert results[0]["content"] == "Customer asked about jacket returns."
    assert provider.search(fashion, "headphone") == []
    assert provider.path_for(fashion).exists()
    assert provider.path_for(electronics).exists()
