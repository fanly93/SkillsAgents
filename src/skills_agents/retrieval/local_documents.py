from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class LocalDocumentRetriever:
    def __init__(self, tenant_paths: dict[str, list[str | Path]]):
        self.tenant_paths = {
            tenant_id: [Path(path) for path in paths]
            for tenant_id, paths in tenant_paths.items()
        }

    def retrieve(self, tenant_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        query_terms = _terms(query)
        matches: list[dict[str, Any]] = []
        for root in self.tenant_paths.get(tenant_id, []):
            if not root.exists():
                continue
            resolved_root = root.resolve()
            for path in sorted(root.rglob("*")):
                if not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
                    continue
                resolved_path = path.resolve()
                if resolved_root != resolved_path and resolved_root not in resolved_path.parents:
                    continue
                text = resolved_path.read_text(encoding="utf-8")
                score = _score(query_terms, text)
                if score == 0:
                    continue
                matches.append(
                    {
                        "source_id": f"{tenant_id}:{path.stem}",
                        "title": _title(path, text),
                        "path": str(resolved_path),
                        "snippet": _snippet(text, query_terms),
                        "score": float(score),
                    }
                )
        matches.sort(key=lambda item: (-item["score"], item["source_id"]))
        return matches[:limit]


def _terms(text: str) -> set[str]:
    return {term for term in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(term) > 2}


def _score(query_terms: set[str], text: str) -> int:
    document_terms = _terms(text)
    return len(query_terms & document_terms)


def _title(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return path.stem.replace("-", " ").title()


def _snippet(text: str, query_terms: set[str]) -> str:
    lines = [line.strip("# ").strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if _terms(line) & query_terms:
            return line[:240]
    return (lines[0] if lines else "")[:240]
