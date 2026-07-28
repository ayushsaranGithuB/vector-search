# Vector Search SaaS

An AI search platform for multiple projects and datasets, built to show grounded retrieval, citations, and observability in one reusable system.

## What This Is

This repo is being shaped as a SaaS-style knowledge platform rather than a single-purpose demo. Each `project` is a separate searchable workspace with its own sources, retrieval settings, and observability.

The first two demo projects will help show the platform in different contexts while keeping the architecture reusable:

1. Indian motor vehicle rules and regulations
2. A second domain-specific knowledge project that can be added without changing the core platform

## Why It Exists

The goal is to demonstrate how modern vector search systems should work in practice:

- grounded answers with source citations
- keyword, vector, and hybrid retrieval
- clear visibility into why a chunk was selected
- project-level source management and analytics
- a retrieval pipeline that can be inspected end to end

## Core Capabilities

- Highlight the exact retrieved text
- Show cosine similarity and rerank scores
- Explain why each chunk was selected
- Support keyword, vector, and hybrid search
- Show latency for each stage of the pipeline
- Visualise embeddings with UMAP or t-SNE
- Display the retrieval pipeline from query to generation
- Flag unsupported claims when an answer is not backed by citations

## Architecture Overview

- `Next.js` frontend for the user-facing app and admin surfaces
- `FastAPI` backend for ingestion, retrieval, and answer generation
- `Prisma` clients in both apps for project and source metadata
- `Neon`-hosted PostgreSQL for projects, sources, chunks, and ingestion runs
- `Pinecone` for semantic retrieval
- Hybrid search for combining keyword and embedding-based results
- Reranking layer for improving result quality
- Citation layer for grounded answers and source linking
- Observability layer for search quality and iteration

## Implemented Tech Stack

### Frontend

- `Next.js` 16 — App shell, project views, admin surfaces
- `React` 19 — Component-driven UI and interactive search
- `Tailwind CSS` 4 — Utility-first styling
- `shadcn/ui` — Accessible UI primitives (Badge, Button, Card, Input)
- `Prisma Client JS` — Direct Neon reads for project/source metadata
- `lucide-react` — Icons

### Backend

- `FastAPI` — API-first ingestion and retrieval workflow
- `Python` 3.13 — Runtime
- `Pydantic` — Request/response schemas and settings management
- `Prisma Client Python` — Type-safe DB access
- `pypdf` — PDF text extraction
- `httpx` — URL fetching
- `boto3` — Cloudflare R2 (S3-compatible) file storage
- `aio-pika` — CloudAMQP (RabbitMQ) ingestion queue
- `pinecone` — Vector database client

### Data and Storage

- `Neon` PostgreSQL — Managed DB for projects, sources, chunks, ingestion runs
- `Prisma` — Shared schema management (4 models: Project, Source, Chunk, IngestionRun)
- `Pinecone` — Managed vector store with hosted-embedding indexes (`multilingual-e5-large`)
- `Cloudflare R2` — S3-compatible object storage for PDFs
- `CloudAMQP` — Managed RabbitMQ task queue for async ingestion

### Retrieval

- Chunking pipeline (1000 chars, 200-char overlap)
- Keyword search (PostgreSQL `CONTAINS` fallback)
- Vector search (Pinecone semantic retrieval, per-project namespaces)
- Hybrid retrieval (vector + keyword combined)

### AI and Models

- `Pinecone Inference` — Embeddings via `multilingual-e5-large` (batched 96/req)
- LLM for grounded answer generation — *not yet implemented*

### Observability

- Retrieval traces — *not yet implemented*
- Query analytics — *not yet implemented*
- Evaluation datasets — *not yet implemented*
- Citation inspection — *not yet implemented*

### Deployment

- Environment-based configuration (`.env`)
- Local development first, deployable later

## Documentation

- [Project goals](./docs/PROJECT_GOALS.MD)
- [Project structure](./docs/PROJECT_STRUCTURE.MD)
- [Tech stack](./docs/TECH_STACK.MD)
- [Build stages](./docs/BUILD_STAGES.MD)
