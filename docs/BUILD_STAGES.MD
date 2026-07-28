# Stage 1: Foundation ✅

- [x] Set up the `FastAPI` backend structure
- [x] Set up the `Next.js` frontend structure
- [x] Wire up managed service configuration for Neon PostgreSQL, Pinecone, CloudAMQP, and Cloudflare R2
- [x] Document Prisma config for the frontend and keep backend Prisma Python schema-based
- [x] Define the core project, source, and chunk concepts (4 Prisma models: Project, Source, Chunk, IngestionRun)
- [x] Build a minimal ingestion path for one project (PDF & URL ingestion via queue → worker → chunk → embed → upsert)

# Stage 2: Retrieval ✅

- [x] Import source documents (PDFs via Cloudflare R2 upload, URLs via httpx fetch)
- [x] Chunk documents consistently (1000 chars with 200-char overlap)
- [x] Generate embeddings (Pinecone Inference `multilingual-e5-large` model, batched 96/req)
- [x] Support semantic search through Pinecone, including hosted-embedding indexes and per-project namespaces
- [x] Store source metadata for filtering (hybrid search: vector + PostgreSQL keyword fallback)

# Stage 3: Grounded Answers

- [x] Add hybrid search (Pinecone vector search → PostgreSQL `CONTAINS` keyword fallback)
- [x] Add citations and source highlighting (score badges, source names, chunk content in results)
- [x] Build the first query UI in `Next.js` (search-layout with loading skeletons, empty states, results cards)
- [ ] Return grounded answers from the backend (requires LLM integration — currently returns chunks, not generated answers)
- [ ] Support opening source passages from answers

# Stage 4: Quality And Observability

- [ ] Add reranking
- [ ] Add query analytics
- [ ] Add evaluation datasets
- [ ] Add retrieval traces
- [ ] Add related-document or cross-link views

# Stage 5: Multi-Project SaaS Polish

- [x] Admin dashboard for per-project source management (create, cancel, delete, auto-polling)
- [x] Public project search pages (per-project namespace isolation)
- [ ] Add a second demo project
- [ ] Improve admin/project dashboards
- [ ] Add Docker-based local and deployment support
- [ ] Polish the README and docs
- [ ] Record a demo flow and tighten performance



