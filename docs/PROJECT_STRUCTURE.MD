# Project Structure

This repo is organized around product areas so the platform can grow into multiple projects without changing the core architecture.

## Frontend

- `Next.js` app shell
- Public homepage and project selection
- Search experience for each project
- Admin surface for project management
- Source management and observability views

## Backend

- `FastAPI` API layer
- Project and source management endpoints
- Ingestion pipeline
- Chunking and embedding workflow
- Retrieval pipeline
- Answer generation and citation assembly

## Product Concepts

- `Project`
  - A searchable workspace with its own sources and retrieval settings
- `Source`
  - A document collection attached to a project
- `Chunk`
  - A retrievable unit derived from a source
- `Retrieval`
  - Keyword, vector, or hybrid lookup over chunks
- `Citation`
  - A link from an answer back to source evidence
- `Observability`
  - Search traces, quality metrics, and evaluation views

## Expansion Model

- Add a new project by registering its metadata, sources, and retrieval settings
- Reuse the same ingestion and retrieval pipeline across all projects
- Keep project-specific behavior in configuration and data rather than separate code paths
