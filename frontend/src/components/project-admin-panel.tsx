"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { ProjectRecord, ProjectSource, SourceType } from "@/lib/projects";

interface ProjectAdminPanelProps {
  project: ProjectRecord;
}

export function ProjectAdminPanel({ project }: ProjectAdminPanelProps) {
  const [sources, setSources] = useState<ProjectSource[]>(project.sources);
  const [sourceType, setSourceType] = useState<SourceType>("pdf");
  const [name, setName] = useState("");
  const [sourceValue, setSourceValue] = useState("");
  const [notes, setNotes] = useState("");
  const [selectedFileName, setSelectedFileName] = useState("");
  const [statusMessage, setStatusMessage] = useState("");

  const totals = sources.reduce(
    (acc, source) => {
      acc.totalChunks += source.chunks;
      acc.processed += source.status === "processed" ? 1 : 0;
      acc.queued += source.status === "queued" ? 1 : 0;
      acc.failed += source.status === "failed" ? 1 : 0;
      return acc;
    },
    { totalChunks: 0, processed: 0, queued: 0, failed: 0 },
  );

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedName = name.trim();
    const trimmedValue = sourceValue.trim();

    if (!trimmedName || !trimmedValue) {
      setStatusMessage("Add a source name and either a PDF file or a URL to continue.");
      return;
    }

    const now = new Date();
    const addedAt = now.toISOString().slice(0, 10);
    const displaySource =
      sourceType === "pdf"
        ? selectedFileName || trimmedValue
        : trimmedValue;

    const nextSource: ProjectSource = {
      id: `local-${Date.now()}`,
      name: trimmedName,
      type: sourceType,
      source: displaySource,
      addedAt,
      size: sourceType === "pdf" ? "Pending upload" : "Pending fetch",
      chunks: 0,
      status: "queued",
      lastSynced: "Queued for ingestion",
    };

    setSources((current) => [nextSource, ...current]);
    setName("");
    setSourceValue("");
    setNotes("");
    setSelectedFileName("");
    setStatusMessage(`${trimmedName} was added locally and is waiting for ingestion.`);
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-16 lg:px-8">
      <div className="flex flex-col gap-4 border-b border-border pb-8 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <Badge variant="secondary" className="mb-4 w-fit">
            Project Admin
          </Badge>
          <h1 className="text-4xl font-bold tracking-tight">{project.name}</h1>
          <p className="mt-3 max-w-2xl text-lg text-muted-foreground">{project.description}</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link href="/projects">
            <Button variant="outline">Back to Projects</Button>
          </Link>
          <Button>Sync Sources</Button>
        </div>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle>Project Stats</CardTitle>
            <CardDescription>Source coverage and ingestion summary.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <StatRow label="Sources" value={String(sources.length)} />
            <StatRow label="Processed" value={String(totals.processed)} />
            <StatRow label="Queued" value={String(totals.queued)} />
            <StatRow label="Failed" value={String(totals.failed)} />
            <StatRow label="Chunks" value={String(totals.totalChunks)} />
          </CardContent>
        </Card>

        <Card className="border-border/50 lg:col-span-2">
          <CardHeader>
            <CardTitle>Add Source</CardTitle>
            <CardDescription>
              Add a PDF or a URL now. This form is local-only for the scaffold and will connect to
              the backend ingestion API next.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4" onSubmit={handleSubmit}>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant={sourceType === "pdf" ? "default" : "outline"}
                  onClick={() => setSourceType("pdf")}
                >
                  PDF
                </Button>
                <Button
                  type="button"
                  variant={sourceType === "url" ? "default" : "outline"}
                  onClick={() => setSourceType("url")}
                >
                  URL
                </Button>
              </div>

              <div className="grid gap-2">
                <label htmlFor="source-name" className="text-sm font-medium">
                  Source name
                </label>
                <Input
                  id="source-name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Motor Vehicles Act, 1988"
                />
              </div>

              {sourceType === "pdf" ? (
                <div className="grid gap-2">
                  <label htmlFor="source-file" className="text-sm font-medium">
                    PDF file
                  </label>
                  <Input
                    id="source-file"
                    type="file"
                    accept="application/pdf"
                    onChange={(event) => {
                      const file = event.target.files?.[0];
                      setSelectedFileName(file?.name ?? "");
                      setSourceValue(file?.name ?? "");
                    }}
                  />
                  <p className="text-xs text-muted-foreground">
                    The backend will later upload and extract text from this PDF.
                  </p>
                </div>
              ) : (
                <div className="grid gap-2">
                  <label htmlFor="source-url" className="text-sm font-medium">
                    Source URL
                  </label>
                  <Input
                    id="source-url"
                    value={sourceValue}
                    onChange={(event) => setSourceValue(event.target.value)}
                    placeholder="https://example.com/source"
                  />
                  <p className="text-xs text-muted-foreground">
                    The backend will later fetch and ingest this URL.
                  </p>
                </div>
              )}

              <div className="grid gap-2">
                <label htmlFor="source-notes" className="text-sm font-medium">
                  Notes
                </label>
                <textarea
                  id="source-notes"
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  rows={4}
                  placeholder="Describe why this source matters and what should happen during ingestion."
                  className="rounded-md border border-input bg-background px-3 py-2 text-sm outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring"
                />
              </div>

              <div className="flex flex-wrap gap-3">
                <Button type="submit">Add Source</Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setName("");
                    setSourceValue("");
                    setNotes("");
                    setSelectedFileName("");
                  }}
                >
                  Reset
                </Button>
              </div>

              {statusMessage ? (
                <p className="text-sm text-muted-foreground">{statusMessage}</p>
              ) : (
                <p className="text-xs text-muted-foreground">
                  Source metadata will later be stored in managed Postgres, while embeddings go to
                  Pinecone.
                </p>
              )}
            </form>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8">
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle>Sources</CardTitle>
            <CardDescription>Track what has been added, processed, and chunked.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-hidden rounded-lg border border-border/60">
              <div className="grid grid-cols-7 gap-4 border-b border-border bg-muted/40 px-4 py-3 text-sm font-medium">
                <span className="col-span-2">Source</span>
                <span>Type</span>
                <span>Status</span>
                <span>Added</span>
                <span>Size</span>
                <span>Chunks</span>
                <span>Synced</span>
              </div>
              <div className="divide-y divide-border">
                {sources.map((source) => (
                  <div key={source.id} className="grid grid-cols-7 gap-4 px-4 py-4 text-sm">
                    <div className="col-span-2">
                      <p className="font-medium">{source.name}</p>
                      <p className="text-muted-foreground">{source.source}</p>
                    </div>
                    <div className="capitalize text-muted-foreground">{source.type}</div>
                    <div>
                      <Badge variant={badgeVariantForStatus(source.status)}>{source.status}</Badge>
                    </div>
                    <div className="text-muted-foreground">{source.addedAt}</div>
                    <div className="text-muted-foreground">{source.size}</div>
                    <div className="text-muted-foreground">{source.chunks}</div>
                    <div className="text-muted-foreground">{source.lastSynced}</div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-border pb-3 last:border-b-0 last:pb-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  );
}

function badgeVariantForStatus(status: ProjectSource["status"]) {
  if (status === "processed") return "default";
  if (status === "failed") return "destructive";
  return "secondary";
}
