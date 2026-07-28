# Tech Stack

## Frontend

- `Next.js`
  - Chosen for the main app shell, project views, and admin surfaces
- `React`
  - Used for component-driven UI and interactive search experiences
- `Tailwind CSS`
  - Keeps the UI fast to iterate on and easy to style consistently
- `shadcn/ui`
  - Provides accessible, composable UI primitives for dashboards and forms

## Backend

- `FastAPI`
  - Fits the planned API-first ingestion and retrieval workflow
- `Python`
  - Useful for retrieval pipelines, document processing, and AI tooling
- `Pydantic`
  - Good fit for strict request and response schemas

## Data and Storage

- `Managed PostgreSQL`
  - Central store for projects, sources, metadata, and application state
- `Pinecone`
  - Managed vector store for semantic retrieval from day one
- File/object storage
  - Stores raw documents and extracted content

## Retrieval and Search

- Chunking pipeline
  - Breaks source documents into retrievable units
- Keyword search
  - Supports exact-match and lexical retrieval
- Vector search
  - Supports semantic retrieval from embeddings
- Hybrid retrieval
  - Combines lexical and semantic results
- Reranking
  - Improves relevance before generation

## AI and Generation

- Embeddings provider to be selected during implementation
  - Needed for semantic search and similarity scoring
- LLM provider to be selected during implementation
  - Used for grounded answer generation
- Optional reranker model or API
  - Improves ranking quality for top results

## Observability

- Retrieval traces
  - Show what was searched and why a result was selected
- Evaluation datasets
  - Support repeatable quality checks
- Query analytics
  - Help track usage and failure modes
- Citation inspection
  - Makes grounded answers easier to verify

## Deployment

- Docker
  - Keeps local development and deployment consistent
- Environment variables
  - Separate configuration from code, including Pinecone credentials
- Local-first workflow
  - Keep the initial setup simple and reproducible

## Deferred Alternatives

- `Weaviate`
  - Good alternative if you want a different managed vector platform later
- `Neo4j`
  - Best introduced as a graph layer for relationships and cross-links
- `LangChain` or `LlamaIndex`
  - Useful if orchestration complexity grows, but not required to define the base platform
- Separate microservices
  - Not needed until the monolith stops being easy to maintain
