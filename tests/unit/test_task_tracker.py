from skills_agents.core.context import TenantContext


def test_task_tracker_creates_updates_and_summarizes_markdown(tmp_path):
    from skills_agents.storage.paths import TenantPathResolver
    from skills_agents.tasks.tracker import TaskTracker

    context = TenantContext(
        tenant_id="fashion_store",
        user_id="user_demo",
        session_id="sess_001",
    )
    tracker = TaskTracker(TenantPathResolver(tmp_path))

    tracker.create_plan(
        context,
        goal="Answer return policy question",
        tasks=[
            {"task_id": "T001", "description": "Identify return intent"},
            {"task_id": "T002", "description": "Check tenant policy"},
            {"task_id": "T003", "description": "Escalate if high risk"},
        ],
    )
    tracker.mark_done(context, "T001", note="Intent identified")
    tracker.mark_failed(context, "T003", reason="High risk refund request")

    markdown = tracker.get_markdown(context)
    summary = tracker.summary(context)

    assert "# Task Plan: sess_001" in markdown
    assert "- [x] T001 Identify return intent" in markdown
    assert "- [ ] T002 Check tenant policy" in markdown
    assert "- [✗] T003 Escalate if high risk" in markdown
    assert "Reason: High risk refund request" in markdown
    assert summary == {"total": 3, "completed": 1, "failed": 1, "pending": 1}


def test_task_tracker_blocks_cross_tenant_reads(tmp_path):
    from skills_agents.storage.paths import TenantPathResolver
    from skills_agents.tasks.tracker import TaskTracker

    tracker = TaskTracker(TenantPathResolver(tmp_path))
    fashion = TenantContext(
        tenant_id="fashion_store",
        user_id="user_demo",
        session_id="sess_001",
    )
    electronics = TenantContext(
        tenant_id="electronics_store",
        user_id="user_demo",
        session_id="sess_001",
    )

    tracker.create_plan(
        fashion,
        goal="Fashion task",
        tasks=[{"task_id": "T001", "description": "Fashion only"}],
    )

    assert "Fashion only" in tracker.get_markdown(fashion)
    assert tracker.get_markdown(electronics) == ""


def test_task_tracker_replaces_existing_note_for_repeated_updates(tmp_path):
    from skills_agents.storage.paths import TenantPathResolver
    from skills_agents.tasks.tracker import TaskTracker

    context = TenantContext(
        tenant_id="fashion_store",
        user_id="user_demo",
        session_id="sess_001",
    )
    tracker = TaskTracker(TenantPathResolver(tmp_path))
    tracker.create_plan(
        context,
        goal="Answer return policy question",
        tasks=[{"task_id": "T001", "description": "Identify return intent"}],
    )

    tracker.mark_done(context, "T001", note="First note")
    tracker.mark_done(context, "T001", note="Second note")

    markdown = tracker.get_markdown(context)
    assert "Second note" in markdown
    assert "First note" not in markdown
    assert markdown.count("Note:") == 1
