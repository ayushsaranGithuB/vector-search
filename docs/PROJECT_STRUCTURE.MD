# Project Structure

This repo is organized around product areas so the platform can grow into multiple projects without changing the core architecture.

## Frontend

- `Next.js` app shell
- Public homepage and project selection
- Search experience for each project (hybrid search with score badges, loading skeletons, empty states)
- Admin surface for project management (source CRUD, auto-polling for active sources)
- Source management (add PDF/URL sources, cancel/delete, status tracking)

## Backend

- `FastAPI` API layer (12 endpoints)
- Project and source management endpoints
- Ingestion pipeline (PDF text extraction, URL fetching, chunking, embedding)
- Chunking and embedding workflow (1000-char chunks, 200-char overlap, Pinecone Inference)
- Retrieval pipeline (Pinecone vector search → PostgreSQL keyword fallback)
- Answer generation and citation assembly — *not yet implemented*
- Async worker for queue-based ingestion (CloudAMQP consumer)

## Product Concepts

- `Project`
  - A searchable workspace with its own sources and retrieval settings
  - Isolated by Pinecone namespace for vector data
- `Source`
  - A document (PDF) or web page (URL) attached to a project
  - Tracks ingestion status: QUEUED → PROCESSING → PROCESSED / FAILED / CANCELLED
- `Chunk`
  - A retrievable unit derived from a source (1000 chars with overlap)
  - Stored in both PostgreSQL (metadata) and Pinecone (vector embedding)
- `IngestionRun`
  - Tracks each ingestion attempt with status, timing, and error messages
- `Retrieval`
  - Keyword (PostgreSQL), vector (Pinecone), or hybrid lookup over chunks
- `Citation`
  - A link from an answer back to source evidence — *not yet implemented*
- `Observability`
  - Search traces, quality metrics, and evaluation views — *not yet implemented*

## Expansion Model

- Add a new project by registering its metadata, sources, and retrieval settings
- Reuse the same ingestion and retrieval pipeline across all projects
- Keep project-specific behavior in configuration and data rather than separate code paths
