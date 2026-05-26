def test_local_document_retriever_ignores_symlinked_files_that_escape_root(tmp_path):
    from skills_agents.retrieval.local_documents import LocalDocumentRetriever

    root = tmp_path / "knowledge"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "secret.md").write_text("# Secret\nReturn policy from another tenant.", encoding="utf-8")
    (root / "secret.md").symlink_to(outside / "secret.md")

    retriever = LocalDocumentRetriever({"fashion_store": [root]})

    assert retriever.retrieve("fashion_store", "return policy") == []
