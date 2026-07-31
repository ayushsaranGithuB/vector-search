import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ArrowRight,
  BrainCircuit,
  Cloud,
  Database,
  FileText,
  Search,
  ShieldCheck,
  Workflow,
  BarChart3,
  Layers,
  Form,
  Route,
  Eye,
} from "lucide-react";

const howItWorks = [
  {
    title: "1. Ingest Documents",
    description:
      "Each project has its own set of sources — PDFs uploaded to Cloudflare R2 or web pages fetched via HTTP. When a source is added, the backend queues an ingestion job in RabbitMQ (CloudAMQP).",
    icon: <FileText size={20} />,
  },
  {
    title: "2. Chunk & Embed",
    description:
      "A background worker pulls the job, extracts text (using pypdf for PDFs or httpx + html parsing for URLs), splits it into overlapping chunks (1000 chars, 200 overlap), and generates embeddings via Pinecone's hosted multilingual-e5-large model in batches of 96.",
    icon: <BrainCircuit size={20} />,
  },
  {
    title: "3. Store in Pinecone",
    description:
      "Chunks and their vector embeddings are upserted into a Pinecone index. Each project lives in its own namespace, so a single shared index can serve many isolated searchable spaces.",
    icon: <Database size={20} />,
  },
  {
    title: "4. Search (Hybrid Retrieval)",
    description:
      "When a user searches, their query is first spell-corrected (fixing typos like 'learners lisense' → 'learner's license'), then embedded via Pinecone Inference for vector search. A PostgreSQL keyword fallback (CONTAINS) runs simultaneously for lexical matching. An initial candidate list is merged from both paths.",
    icon: <Search size={20} />,
  },
  {
    title: "5. Rerank Results",
    description:
      "Initial candidates are re-scored by a Cohere cross-encoder model for improved precision at the top of the list. The reranker considers semantic relevance between the query and each result, producing a more accurate ranking than vector similarity alone.",
    icon: <Layers size={20} />,
  },
  {
    title: "6. Return Results with Citations",
    description:
      "Each result includes the chunk content, its source document name, a relevance score, and a citation link. Matched query terms are highlighted in the results, skipping common words. The frontend displays everything in a clean card layout so users can inspect exactly why each result was returned.",
    icon: <ShieldCheck size={20} />,
  },
  {
    title: "7. Generate AI Summary (Optional)",
    description:
      "Users can click 'Generate AI Summary' to produce a grounded answer. The backend sends the top results to OpenRouter (Qwen 3.7 Flash) which generates a natural language summary with numbered citations — each mapped directly to a source document.",
    icon: <BrainCircuit size={20} />,
  },
  {
    title: "8. Observe & Debug",
    description:
      "Every search query, LLM call, and error is logged to a local JSONL file via loguru. The admin observability dashboard (at /admin/observability) reads these logs and displays real-time metrics: query latency, source IDs, token counts, estimated cost, and error messages.",
    icon: <BarChart3 size={20} />,
  },
];

const coreCapabilities = [
  {
    title: "Grounded Answers",
    description:
      "Answers backed by source citations with LLM-generated summaries — each claim mapped to numbered source links.",
    lucideIcon: <Route size={18} />,
  },
  {
    title: "Hybrid Search",
    description:
      "Keyword, vector, and hybrid retrieval combined for the best results across semantic and exact-match queries.",
    lucideIcon: <Search size={18} />,
  },
  {
    title: "Reranking",
    description:
      "Cohere cross-encoder re-scores initial candidates for improved precision at the top of the result list.",
    lucideIcon: <Layers size={18} />,
  },
  {
    title: "Spell Correction",
    description:
      "Automatic typo fixing in user queries — 'learners lisense' becomes 'learner's license' before retrieval.",
    lucideIcon: <Eye size={18} />,
  },
  {
    title: "Full Observability",
    description:
      "Search queries, LLM token usage and cost, latency, and errors — logged to JSONL and displayed on the admin dashboard.",
    lucideIcon: <BarChart3 size={18} />,
  },
  {
    title: "Multi-Project SaaS",
    description:
      "Each project is a separate searchable workspace with its own sources, Pinecone namespace, and settings.",
    lucideIcon: <Form size={18} />,
  },
];

const techStack = [
  {
    title: "Frontend",
    items: [
      {
        label: "Next.js 16 + React 19",
        why: "App shell, project views, and admin surfaces — SSR for fast loads, RSC where helpful.",
      },
      {
        label: "Tailwind CSS 4 + shadcn/ui",
        why: "Rapid, consistent UI development with accessible primitives.",
      },
      {
        label: "Prisma Client JS",
        why: "Reads project and source metadata directly from Neon with full type safety.",
      },
    ],
    icon: <Cloud size={18} />,
  },
  {
    title: "Backend",
    items: [
      {
        label: "FastAPI (Python 3.13)",
        why: "Async-first API for ingestion and retrieval — fast to build, easy to keep correct with Pydantic schemas.",
      },
      {
        label: "Prisma Client Python",
        why: "Shares the same schema as the frontend for type-safe metadata access.",
      },
      {
        label: "Pinecone SDK",
        why: "Vector database client for semantic search; the hosted-embedding index means we send plain text and get vectors back automatically.",
      },
      {
        label: "aio-pika + CloudAMQP",
        why: "Async RabbitMQ queue makes ingestion resilient — jobs survive restarts and scale horizontally.",
      },
      {
        label: "boto3 + Cloudflare R2",
        why: "S3-compatible object storage for raw PDFs; S3 API means zero vendor lock-in.",
      },
    ],
    icon: <Workflow size={18} />,
  },
  {
    title: "Data & Infrastructure",
    items: [
      {
        label: "Neon PostgreSQL",
        why: "Serverless Postgres with branching — ideal for per-environment schema iteration.",
      },
      {
        label: "Pinecone (Managed Vector Store)",
        why: "Handles the hard part of ANN search at scale; multilingual-e5-large gives strong multi-language retrieval.",
      },
      {
        label: "Cloudflare R2",
        why: "Zero egress fees for stored PDFs, global edge network.",
      },
      {
        label: "CloudAMQP (Managed RabbitMQ)",
        why: "Reliable async job queue without managing infrastructure.",
      },
    ],
    icon: <Database size={18} />,
  },
  {
    title: "Retrieval Pipeline",
    items: [
      {
        label: "Chunking Pipeline",
        why: "Splits documents into overlapping 1000-character chunks (200 overlap) for precise retrieval while preserving context across boundaries.",
      },
      {
        label: "Keyword Search",
        why: "PostgreSQL CONTAINS fallback catches exact matches (part numbers, legal citations, proper names) that vector search can miss.",
      },
      {
        label: "Vector Search",
        why: "Pinecone ANN search over multilingual-e5-large embeddings for semantic understanding across languages.",
      },
      {
        label: "Hybrid Retrieval",
        why: "Merges keyword and vector results into a single ranked list, combining the strengths of both approaches.",
      },
      {
        label: "Spell Correction",
        why: "Automatic typo fixing (query_normalizer.py) fixes common misspellings before retrieval — e.g. 'learners lisense' → 'learner's license'.",
      },
      {
        label: "Reranking (Cohere)",
        why: "Cross-encoder model re-ranks initial search results for better precision at the top of the list, improving over pure vector similarity.",
      },
    ],
    icon: <Search size={18} />,
  },
  {
    title: "AI & Models",
    items: [
      {
        label: "Embeddings (multilingual-e5-large)",
        why: "Pinecone's hosted model generates 1024-dim vectors from plain text — no separate embedding infrastructure needed.",
      },
      {
        label: "LLM for Generation (Qwen 3.7 Flash)",
        why: "OpenRouter-hosted model generates grounded answers with numbered citations from retrieved chunks. Cost: $0.03/M input tokens, $0.13/M output tokens.",
      },
      {
        label: "Reranker Model (Cohere)",
        why: "Cross-encoder re-ranks initial search results for improved relevance ordering at the top of the list.",
      },
    ],
    icon: <BrainCircuit size={18} />,
  },
  {
    title: "Observability",
    items: [
      {
        label: "Query Analytics (loguru JSONL)",
        why: "Every search query, LLM call (with token counts and cost), latency, and error is logged to a local JSONL file — no database dependency for observability.",
      },
      {
        label: "Observability Dashboard",
        why: "Admin page at /admin/observability reads the JSONL log file and displays real-time metrics with cards for each event type.",
      },
    ],
    icon: <BarChart3 size={18} />,
  },
];

const designDecisions = [
  {
    title: "Why hybrid search?",
    description:
      "Vector search alone can miss exact keyword matches (part numbers, legal citations, proper names). PostgreSQL CONTAINS provides a simple lexical fallback that catches these cases with zero extra infrastructure.",
  },
  {
    title: "Why reranking after vector search?",
    description:
      "Vector similarity (cosine distance) is a good first pass but can miss nuanced relevance. A cross-encoder like Cohere re-scores each candidate specifically against the query, producing a much sharper ranking at the cost of a second inference pass.",
  },
  {
    title: "Why Pinecone namespaces over separate indexes?",
    description:
      "One shared index with per-project namespaces keeps operations simple — no need to provision, monitor, or pay for separate indexes per project. Each project's data is isolated at the namespace level.",
  },
  {
    title: "Why async ingestion with RabbitMQ?",
    description:
      "PDF parsing and embedding generation take time. Queuing the work decouples the API from processing — the user gets an immediate response and the worker processes jobs as capacity allows.",
  },
  {
    title: "Why spell correction before search?",
    description:
      "Vector search is robust to minor typos, but keyword fallback (CONTAINS) is not. Correcting typos before retrieval ensures both paths work well — and the UI can highlight the corrected terms for transparency.",
  },
  {
    title: "Why loguru JSONL files instead of a database for analytics?",
    description:
      "Observability data is append-only, high-volume, and doesn't need ACID semantics. Writing to a local JSONL file via loguru is simpler, faster, and doesn't add load to the primary database. Rotation and retention are handled by loguru's built-in file management.",
  },
  {
    title: "Why not LangChain / LlamaIndex?",
    description:
      "This project's retrieval pipeline is straightforward: chunk → embed → search → rerank → generate. Adding an orchestration framework would introduce abstraction overhead without meaningful benefit. The direct approach is easier to debug, extend, and understand.",
  },
  {
    title: "Why Prisma across both frontend and backend?",
    description:
      "A single Prisma schema file shared by TypeScript (Next.js) and Python (FastAPI) keeps the data model in one place. Changes to the schema are reviewed once and applied everywhere, preventing drift.",
  },
];

export default function DocsPage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-border">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/5" />
        <div className="relative mx-auto max-w-6xl px-6 py-24 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <Badge variant="secondary" className="mb-6 text-sm px-4 py-1.5">
              How It Works
            </Badge>
            <h1 className="text-5xl font-bold tracking-tight sm:text-6xl">
              Architecture &amp; Design
            </h1>
            <p className="mt-6 text-xl leading-8 text-muted-foreground">
              A deep dive into how Vector Search SaaS works — from document
              ingestion to hybrid retrieval — and why each technology was
              chosen.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works Pipeline */}
      <section className="border-b border-border">
        <div className="mx-auto max-w-6xl px-6 py-24 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight">
              The Retrieval Pipeline
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              From raw document to ranked search results in five steps.
            </p>
          </div>

          <div className="mt-16 space-y-14 max-w-3xl mx-auto">
            {howItWorks.map((step, index) => (
              <div key={step.title} className="relative">
                <div className="relative border-0 border-none">
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <div className=" text-primary">{step.icon}</div>
                      <CardTitle className="text-xl">{step.title}</CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent className="mt-4">
                    <CardDescription className="text-base leading-relaxed">
                      {step.description}
                    </CardDescription>
                  </CardContent>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Core Capabilities */}
      <section className="border-t border-border bg-muted/30">
        <div className="mx-auto max-w-6xl px-6 py-24 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-4xl font-bold tracking-tight">
              Core Capabilities
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Modern vector search systems should work in practice - here is
              what this platform delivers.
            </p>
          </div>
          <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {coreCapabilities.map((capability) => (
              <Card
                key={capability.title}
                className="border-border/50 transition-colors hover:border-border px-3 py-6"
              >
                <CardHeader>
                  <CardTitle className="text-xl flex gap-2 items-center">
                    {capability.lucideIcon && (
                      <span className="text-sm">{capability.lucideIcon}</span>
                    )}
                    {capability.title}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-sm leading-relaxed">
                    {capability.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="border-b border-border bg-muted/30">
        <div className="mx-auto max-w-6xl px-6 py-24 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight">
              Technology Choices
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              The tools powering each layer of the platform and the reasoning
              behind them.
            </p>
          </div>

          <div className="mt-16 grid gap-8 lg:grid-cols-3">
            {techStack.map((layer) => (
              <Card
                key={layer.title}
                className="border-border/50 transition-colors hover:border-border"
              >
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <span className="text-primary">{layer.icon}</span>
                    <CardTitle className="text-lg">{layer.title}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {layer.items.map((item) => (
                    <div key={item.label}>
                      <p className="text-sm font-medium">{item.label}</p>
                      <p className="mt-1 text-sm text-muted-foreground leading-relaxed">
                        {item.why}
                      </p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Design Decisions */}
      <section className="border-b border-border">
        <div className="mx-auto max-w-6xl px-6 py-24 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight">
              Design Decisions
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Why the platform is built this way — trade-offs, rationale, and
              lessons learned.
            </p>
          </div>

          <div className="mt-16 space-y-6">
            {designDecisions.map((decision) => (
              <Card
                key={decision.title}
                className="border-border/50 transition-colors hover:border-border"
              >
                <CardHeader>
                  <div className="flex items-start gap-3">
                    <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-primary" />
                    <div>
                      <CardTitle className="text-lg">
                        {decision.title}
                      </CardTitle>
                      <CardDescription className="mt-2 text-base leading-relaxed">
                        {decision.description}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Project Status Summary */}
      <section className="bg-muted/30">
        <div className="mx-auto max-w-6xl px-6 py-24 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight">
              Current Status
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Where the platform is today and what's coming next.
            </p>
          </div>

          <div className="mt-16 grid gap-6 sm:grid-cols-2">
            <Card className="border-border/50">
              <CardHeader>
                <Badge
                  variant="secondary"
                  className="mb-2 w-fit px-3 py-1 text-sm"
                >
                  ✅ Implemented
                </Badge>
                <CardTitle className="text-lg">Core Retrieval</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-green-500" />
                    PDF &amp; URL ingestion with async job queue
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-green-500" />
                    Chunking (1000 chars, 200 overlap)
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-green-500" />
                    Vector + keyword hybrid search
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-green-500" />
                    Per-project namespace isolation
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-green-500" />
                    Admin dashboard with source management
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-green-500" />
                    Public per-project search pages
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-green-500" />
                    LLM-grounded answers with numbered citations
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-green-500" />
                    Reranking (Cohere cross-encoder)
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-green-500" />
                    Spell correction for user queries
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-green-500" />
                    Search term highlighting
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-green-500" />
                    Query analytics &amp; observability dashboard
                  </li>
                </ul>
              </CardContent>
            </Card>

            <Card className="border-border/50">
              <CardHeader>
                <Badge
                  variant="outline"
                  className="mb-2 w-fit px-3 py-1 text-sm text-muted-foreground"
                >
                  🚧 In Progress / Planned
                </Badge>
                <CardTitle className="text-lg">Upcoming Work</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                    Evaluation datasets for quality measurement
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                    Retrieval traces (per-query pipeline tracing)
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                    Related-document and cross-link views
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                    Second demo project
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                    Docker-based local and deployment support
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                    Wire up "Sync Sources" button in admin panel
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                    Populate pinecone_vector_id on chunks after upsert
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>
    </>
  );
}
