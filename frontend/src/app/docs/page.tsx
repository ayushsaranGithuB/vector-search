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
  BookOpen,
  BrainCircuit,
  Cloud,
  Database,
  FileText,
  GitBranch,
  Search,
  ShieldCheck,
  Workflow,
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
      "When a user searches, the query is embedded via Pinecone Inference and used for a vector search. Simultaneously, a PostgreSQL keyword fallback (CONTAINS) runs for lexical matching. Results from both paths are merged into a single ranked list.",
    icon: <Search size={20} />,
  },
  {
    title: "5. Return Results with Citations",
    description:
      "Each result includes the chunk content, its source document name, a relevance score, and a citation link. The frontend displays everything in a clean card layout so users can inspect exactly why each result was returned.",
    icon: <ShieldCheck size={20} />,
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
];

const designDecisions = [
  {
    title: "Why hybrid search?",
    description:
      "Vector search alone can miss exact keyword matches (part numbers, legal citations, proper names). PostgreSQL CONTAINS provides a simple lexical fallback that catches these cases with zero extra infrastructure.",
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
    title: "Why not LangChain / LlamaIndex?",
    description:
      "This project's retrieval pipeline is straightforward: chunk → embed → search. Adding an orchestration framework would introduce abstraction overhead without meaningful benefit. The direct approach is easier to debug, extend, and understand.",
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
                    LLM integration for grounded answer generation
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                    Reranking to improve result quality
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                    Query analytics and retrieval traces
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                    Evaluation datasets for quality measurement
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />
                    Docker-based local and deployment support
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
