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
- Managed vector store for semantic retrieval
- Hybrid search for combining keyword and embedding-based results
- Reranking layer for improving result quality
- Citation layer for grounded answers and source linking
- Observability layer for search quality and iteration

## Planned Tech Stack

### Frontend

- `Next.js`
- `React`
- `Tailwind CSS`
- `shadcn/ui`

### Backend

- `FastAPI`
- `Python`
- `Pydantic`

### Data and Storage

- `Managed PostgreSQL`
- `Pinecone`
- Document and metadata storage for projects and sources

### Retrieval

- Chunking pipeline
- Keyword search
- Vector search
- Hybrid retrieval
- Reranking

### AI and Models

- Embeddings model provider to be selected during implementation
- LLM for grounded answer generation
- Optional reranking model or API

### Observability

- Retrieval traces
- Query analytics
- Evaluation datasets
- Citation inspection

### Deployment

- Docker
- Environment-based configuration
- Local development first, deployable later

## Documentation

- [Project goals](./docs/PROJECT_GOALS.MD)
- [Project structure](./docs/PROJECT_STRUCTURE.MD)
- [Tech stack](./docs/TECH_STACK.MD)
- [Build stages](./docs/BUILD_STAGES.MD)
