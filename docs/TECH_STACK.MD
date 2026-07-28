# Tech Stack

## Frontend

- `Next.js` 16
  - Chosen for the main app shell, project views, and admin surfaces
- `React` 19
  - Used for component-driven UI and interactive search experiences
- `Tailwind CSS` 4
  - Keeps the UI fast to iterate on and easy to style consistently
- `shadcn/ui`
  - Provides accessible, composable UI primitives for dashboards and forms
- `Prisma Client JS`
  - Lets the frontend read project and source metadata directly from Neon
- `lucide-react`
  - Icon library for UI elements

## Backend

- `FastAPI`
  - Fits the planned API-first ingestion and retrieval workflow
- `Python` 3.13
  - Runtime for the backend
- `Pydantic`
  - Good fit for strict request and response schemas and settings management
- `Prisma Client Python`
  - Gives the backend a type-safe way to read and write the shared metadata tables
- `pypdf`
  - PDF text extraction for document ingestion
- `httpx`
  - Async HTTP client for fetching URL-based sources
- `boto3`
  - S3-compatible client for Cloudflare R2 file storage
- `aio-pika`
  - Async RabbitMQ client for the CloudAMQP ingestion queue
- `pinecone` SDK
  - Vector database client for semantic search operations

## Data and Storage

- `Neon` PostgreSQL
  - Managed database for projects, sources, chunks, and ingestion runs
- `Prisma schema`
  - Shared model definition for both apps (4 models: Project, Source, Chunk, IngestionRun)
- `Prisma config`
  - Used by both frontend and backend Prisma CLIs to keep the Neon connection string out of `schema.prisma`
- `Pinecone`
  - Managed vector store for semantic retrieval
  - Uses `multilingual-e5-large` hosted-embedding index — query text is passed directly and Pinecone converts it to a vector automatically
  - Uses namespaces for multi-project separation so one shared index can host many project embeddings safely
- `Cloudflare R2`
  - S3-compatible object storage for raw PDF documents
- `CloudAMQP`
  - Managed RabbitMQ task queue for asynchronous document ingestion

## Retrieval and Search

- Chunking pipeline
  - Breaks source documents into retrievable units (1000 chars, 200-char overlap)
- Keyword search
  - PostgreSQL `CONTAINS` fallback for exact-match and lexical retrieval
- Vector search
  - Semantic retrieval via Pinecone Inference embeddings
- Hybrid retrieval
  - Combines lexical (PostgreSQL) and semantic (Pinecone) results
- Reranking
  - *Not yet implemented* — planned for Stage 4

## AI and Generation

- Embeddings provider
  - **Implemented**: Pinecone Inference `multilingual-e5-large` (batched 96 vectors per request)
- LLM provider
  - *Not yet implemented* — needed for grounded answer generation (Stage 3)
- Optional reranker model or API
  - *Not yet implemented* — planned for Stage 4

## Observability

- Retrieval traces
  - *Not yet implemented* — planned for Stage 4
- Evaluation datasets
  - *Not yet implemented* — planned for Stage 4
- Query analytics
  - *Not yet implemented* — planned for Stage 4
- Citation inspection
  - *Not yet implemented* — planned for Stage 4

## Deployment

- Docker
  - *Not yet implemented* — planned for Stage 5
- Environment variables
  - Separate configuration from code, including the shared Neon connection string
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


