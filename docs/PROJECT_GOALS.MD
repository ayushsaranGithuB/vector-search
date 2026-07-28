# Project Goals

## Vision

Build a reusable AI search platform that can power multiple projects and datasets while keeping every answer grounded in cited source material.

The product should feel like a SaaS knowledge workspace:

- each `project` is an isolated searchable space
- each project has its own `sources`, retrieval configuration, and observability
- new projects should be added by configuration and ingestion, not by rewriting the platform

## Product Goals

- Support grounded answers with source citations
- Make retrieval behavior understandable through observability
- Allow keyword, vector, and hybrid search modes
- Support project-level dashboards for sources and search quality
- Make the app easy to extend with new datasets

## Initial Demo Projects

1. Indian motor vehicle rules and regulations
2. A second domain-focused demo project that proves the platform can expand cleanly to another knowledge base

## Success Criteria — Progress

| Criterion | Status |
|-----------|--------|
| A user can pick a project and ask a question | ✅ Done — per-project search pages with hybrid search |
| The answer returns citations tied to source passages | ✅ Done — search returns chunks with source metadata; LLM-generated answers with numbered citations on summary card |
| The UI shows why the result was retrieved | ✅ Done — score badges, source names, chunk content in results |
| Different search modes can be compared | 🟡 Partial — hybrid search works; dedicated mode toggle not yet built |
| A new project can be added without changing core retrieval architecture | ✅ Done — projects are isolated by Pinecone namespace; add via DB + config |

## Primary User Workflows — Progress

| Workflow | Status |
|----------|--------|
| Browse available projects | ✅ Done — `/projects` page lists all projects |
| Add or manage sources inside a project | ✅ Done — admin panel with PDF/URL upload, cancel, delete, auto-polling |
| Ask a question and receive a grounded answer | ✅ Done — "Generate AI Summary" button produces LLM-grounded answer with numbered citations |
| Open citations and inspect source passages | ✅ Done — numbered result cards with clickable citation links from AI summary |
| Review retrieval traces and search quality signals | ❌ Not yet implemented |
| Compare search modes and reranking output | ❌ Not yet implemented |

## Non-Goals For v1

- Full production-grade multi-tenant billing
- Complex role-based enterprise permissions
- Broad public document crawling
- Perfectly complete legal or regulatory coverage
- Advanced workflow automation beyond search and retrieval

## Future Goals

- Add more projects and datasets with minimal setup
- Expand observability and evaluation tooling
- Improve retrieval quality through reranking and better chunking
- Add richer source relationship and cross-linking views
- Support additional deployment targets after the core workflow is stable
