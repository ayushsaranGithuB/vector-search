import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

// Icons
import { BarChart3, Eye, Form, Layers, Route, Search } from "lucide-react";

const coreCapabilities = [
  {
    title: "Grounded Answers",
    description:
      "Answers backed by source citations with highlighted retrieved text.",
    lucideIcon: <Route size={18} />,
  },
  {
    title: "Hybrid Search",
    description:
      "Keyword, vector, and hybrid retrieval combined for the best results.",
    lucideIcon: <Search size={18} />,
  },
  {
    title: "Full Observability",
    description:
      "Cosine similarity scores, rerank scores, and latency for each pipeline stage.",
    lucideIcon: <BarChart3 size={18} />,
  },
  {
    title: "Citation Inspection",
    description:
      "Flag unsupported claims when an answer is not backed by citations.",
    lucideIcon: <Eye size={18} />,
  },
  {
    title: "Embedding Visualisation",
    description:
      "Visualise embeddings with UMAP or t-SNE to understand your data.",
    lucideIcon: <Layers size={18} />,
  },
  {
    title: "Multi-Project SaaS",
    description:
      "Each project is a separate searchable workspace with its own sources and settings.",
    lucideIcon: <Form size={18} />,
  },
];

const architectureLayers = [
  {
    title: "Frontend",
    items: ["Next.js", "React", "Tailwind CSS", "shadcn/ui"],
  },
  {
    title: "Backend",
    items: ["FastAPI", "Python", "Pydantic"],
  },
  {
    title: "Data & Storage",
    items: ["Managed PostgreSQL", "Pinecone", "Document & Metadata Storage"],
  },
  {
    title: "Retrieval Pipeline",
    items: [
      "Chunking Pipeline",
      "Keyword Search",
      "Vector Search",
      "Hybrid Retrieval",
      "Reranking",
    ],
  },
  {
    title: "AI & Models",
    items: ["Embeddings Model", "LLM for Generation", "Reranking Model"],
  },
  {
    title: "Observability",
    items: [
      "Retrieval Traces",
      "Query Analytics",
      "Evaluation Datasets",
      "Citation Inspection",
    ],
  },
];

export default function Home() {
  return (
    <>
      {/* Hero Section */}
      <section className="relative overflow-hidden border-b border-border">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/5" />
        <div className="relative mx-auto max-w-6xl px-6 py-24 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <Badge variant="secondary" className="mb-6 text-sm px-4 py-1.5">
              AI-Powered Search Platform
            </Badge>
            <h1 className="text-5xl font-bold tracking-tight sm:text-7xl">
              Vector Search SaaS
            </h1>
            <p className="mt-6 text-xl leading-8 text-muted-foreground">
              An AI search platform for multiple projects and datasets, built to
              show grounded retrieval, citations, and observability in one
              reusable system.
            </p>
            <div className="mt-10 flex items-center justify-center gap-4">
              <Link href="/projects">
                <Button size="lg" className="text-lg px-8 py-6 h-auto">
                  Browse Projects
                </Button>
              </Link>
              <Link href="/docs">
                <Button
                  size="lg"
                  variant="outline"
                  className="text-lg px-8 py-6 h-auto"
                >
                  Read the Docs
                </Button>
              </Link>
            </div>
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

      {/* Architecture Overview */}
      <section className="mx-auto max-w-6xl px-6 py-24 sm:py-32 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-4xl font-bold tracking-tight">
            Architecture Overview
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            A modular, multi-project platform built for scale and observability.
          </p>
        </div>
        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {architectureLayers.map((layer) => (
            <Card key={layer.title} className="border-border/50">
              <CardHeader>
                <CardTitle className="text-lg">{layer.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {layer.items.map((item) => (
                    <li
                      key={item}
                      className="flex items-center gap-2 text-base text-muted-foreground"
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-primary/60 shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </>
  );
}
