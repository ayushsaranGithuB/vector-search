import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const coreCapabilities = [
  {
    title: "Grounded Answers",
    description: "Answers backed by source citations with highlighted retrieved text.",
  },
  {
    title: "Hybrid Search",
    description: "Keyword, vector, and hybrid retrieval combined for the best results.",
  },
  {
    title: "Full Observability",
    description: "Cosine similarity scores, rerank scores, and latency for each pipeline stage.",
  },
  {
    title: "Citation Inspection",
    description: "Flag unsupported claims when an answer is not backed by citations.",
  },
  {
    title: "Embedding Visualisation",
    description: "Visualise embeddings with UMAP or t-SNE to understand your data.",
  },
  {
    title: "Multi-Project SaaS",
    description: "Each project is a separate searchable workspace with its own sources and settings.",
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
    items: ["Chunking Pipeline", "Keyword Search", "Vector Search", "Hybrid Retrieval", "Reranking"],
  },
  {
    title: "AI & Models",
    items: ["Embeddings Model", "LLM for Generation", "Reranking Model"],
  },
  {
    title: "Observability",
    items: ["Retrieval Traces", "Query Analytics", "Evaluation Datasets", "Citation Inspection"],
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
            <Badge variant="secondary" className="mb-6">
              AI-Powered Search Platform
            </Badge>
            <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
              Vector Search SaaS
            </h1>
            <p className="mt-6 text-lg leading-8 text-muted-foreground">
              An AI search platform for multiple projects and datasets, built to show grounded
              retrieval, citations, and observability in one reusable system.
            </p>
            <div className="mt-10 flex items-center justify-center gap-4">
              <Button size="lg" asChild>
                <Link href="/projects">Browse Projects</Link>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <Link href="/docs">Read the Docs</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Core Capabilities */}
      <section className="mx-auto max-w-6xl px-6 py-24 sm:py-32 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight">Core Capabilities</h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Modern vector search systems should work in practice — here is what this platform
            delivers.
          </p>
        </div>
        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {coreCapabilities.map((capability) => (
            <Card key={capability.title} className="border-border/50 transition-colors hover:border-border">
              <CardHeader>
                <CardTitle className="text-lg">{capability.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-sm">{capability.description}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Architecture Overview */}
      <section className="border-t border-border bg-muted/30">
        <div className="mx-auto max-w-6xl px-6 py-24 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight">Architecture Overview</h2>
            <p className="mt-4 text-lg text-muted-foreground">
              A modular, multi-project platform built for scale and observability.
            </p>
          </div>
          <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {architectureLayers.map((layer) => (
              <Card key={layer.title} className="border-border/50">
                <CardHeader>
                  <CardTitle className="text-base">{layer.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {layer.items.map((item) => (
                      <li key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
                        <span className="h-1.5 w-1.5 rounded-full bg-primary/60" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Demo Projects */}
      <section className="mx-auto max-w-6xl px-6 py-24 sm:py-32 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight">Demo Projects</h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Explore the platform through real-world knowledge domains.
          </p>
        </div>
        <div className="mt-16 grid gap-6 sm:grid-cols-2">
          <Card className="border-border/50 transition-colors hover:border-border">
            <CardHeader>
              <Badge className="mb-2 w-fit">Coming Soon</Badge>
              <CardTitle>Indian Motor Vehicle Rules</CardTitle>
              <CardDescription>
                Search and retrieve information from Indian motor vehicle regulations and
                traffic laws with grounded citations.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" size="sm" disabled>
                View Project
              </Button>
            </CardContent>
          </Card>
          <Card className="border-border/50 transition-colors hover:border-border">
            <CardHeader>
              <Badge className="mb-2 w-fit">Coming Soon</Badge>
              <CardTitle>Domain Knowledge Base</CardTitle>
              <CardDescription>
                A second domain-specific knowledge project demonstrating the platform's
                reusability across different contexts.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" size="sm" disabled>
                View Project
              </Button>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border">
        <div className="mx-auto max-w-6xl px-6 py-8 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <p className="text-sm text-muted-foreground">
              Vector Search SaaS — Built with Next.js, FastAPI, and shadcn/ui
            </p>
            <div className="flex gap-6">
              <Link href="/docs" className="text-sm text-muted-foreground hover:text-foreground">
                Docs
              </Link>
              <Link href="/projects" className="text-sm text-muted-foreground hover:text-foreground">
                Projects
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}