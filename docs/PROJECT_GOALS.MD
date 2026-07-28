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

## Success Criteria

- A user can pick a project and ask a question
- The answer returns citations tied to source passages
- The UI shows why the result was retrieved
- Different search modes can be compared
- A new project can be added without changing core retrieval architecture

## Primary User Workflows

- Browse available projects
- Add or manage sources inside a project
- Ask a question and receive a grounded answer
- Open citations and inspect source passages
- Review retrieval traces and search quality signals
- Compare search modes and reranking output

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
