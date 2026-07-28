"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import Link from "next/link";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  FileText,
  Globe,
  FileUp,
  Trash2,
  XCircle,
  RefreshCw,
  Loader2,
} from "lucide-react";
import type { ProjectRecord, ProjectSource, SourceType } from "@/lib/projects";

interface ProjectAdminPanelProps {
  project: ProjectRecord;
}

export function ProjectAdminPanel({ project }: ProjectAdminPanelProps) {
  const [sources, setSources] = useState<ProjectSource[]>(project.sources);
  const [sourceType, setSourceType] = useState<SourceType>("pdf");
  const [name, setName] = useState("");
  const [sourceValue, setSourceValue] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFileName, setSelectedFileName] = useState("");
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const titleFetchRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const totals = sources.reduce(
    (acc, source) => {
      acc.totalChunks += source.chunks;
      acc.processed += source.status === "processed" ? 1 : 0;
      acc.queued += source.status === "queued" ? 1 : 0;
      acc.failed += source.status === "failed" ? 1 : 0;
      acc.cancelled += source.status === "cancelled" ? 1 : 0;
      return acc;
    },
    { totalChunks: 0, processed: 0, queued: 0, failed: 0, cancelled: 0 },
  );

  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

  async function handleDelete(sourceId: string, sourceName: string) {
    if (
      !confirm(
        `Delete "${sourceName}"? This will remove it from Pinecone, the database, and R2.`,
      )
    )
      return;

    setActionLoading(sourceId);

    const response = await fetch(`${backendUrl}/sources/${sourceId}`, {
      method: "DELETE",
    });

    if (response.ok) {
      setSources((current) => current.filter((s) => s.id !== sourceId));
      toast.success(`"${sourceName}" deleted successfully.`);
    } else {
      const error = await response.text();
      toast.error(`Failed to delete "${sourceName}"`, {
        description: error,
      });
    }
    setActionLoading(null);
  }

  async function handleCancel(sourceId: string, sourceName: string) {
    if (
      !confirm(
        `Cancel "${sourceName}"? This will stop processing and clean up any partial data.`,
      )
    )
      return;

    setActionLoading(sourceId);

    const response = await fetch(`${backendUrl}/sources/${sourceId}/cancel`, {
      method: "POST",
    });

    if (response.ok) {
      setSources((current) =>
        current.map((s) =>
          s.id === sourceId ? { ...s, status: "cancelled" as const } : s,
        ),
      );
      toast.success(`"${sourceName}" cancelled.`);
    } else {
      const error = await response.text();
      toast.error(`Failed to cancel "${sourceName}"`, {
        description: error,
      });
    }
    setActionLoading(null);
  }

  // Poll for source status updates while any source is in a non-terminal state
  const hasActiveSources = sources.some(
    (s) => s.status === "queued" || s.status === "processing",
  );

  const fetchSources = useCallback(async () => {
    try {
      const response = await fetch(
        `${backendUrl}/projects/${project.slug}/sources`,
        { cache: "no-store" },
      );
      if (response.ok) {
        const fresh: ProjectSource[] = await response.json();
        setSources(fresh);
      }
    } catch {
      // Silently retry on next poll
    }
  }, [backendUrl, project.slug]);

  useEffect(() => {
    if (!hasActiveSources) return;

    const interval = setInterval(fetchSources, 5000);
    return () => clearInterval(interval);
  }, [hasActiveSources, fetchSources]);

  // Auto-fetch page title from URL when URL input changes
  useEffect(() => {
    if (sourceType !== "url") {
      if (titleFetchRef.current) clearTimeout(titleFetchRef.current);
      return;
    }

    const trimmed = sourceValue.trim();
    if (!trimmed.startsWith("http://") && !trimmed.startsWith("https://"))
      return;

    if (titleFetchRef.current) clearTimeout(titleFetchRef.current);

    titleFetchRef.current = setTimeout(async () => {
      try {
        const res = await fetch(
          `${backendUrl}/fetch-title?url=${encodeURIComponent(trimmed)}`,
        );
        if (res.ok) {
          const data = await res.json();
          if (data.title) {
            setName(data.title);
          }
        }
      } catch {
        // Silently fail — user can still type a name manually
      }
    }, 800);

    return () => {
      if (titleFetchRef.current) clearTimeout(titleFetchRef.current);
    };
  }, [sourceValue, sourceType, backendUrl]);

  // Clear URL input when switching back to PDF
  useEffect(() => {
    if (sourceType === "pdf") {
      setSourceValue("");
    }
  }, [sourceType]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    let trimmedValue = sourceValue.trim();

    // Auto-prepend https:// if no scheme is provided
    if (
      sourceType === "url" &&
      trimmedValue &&
      !/^https?:\/\//i.test(trimmedValue)
    ) {
      trimmedValue = `https://${trimmedValue}`;
      setSourceValue(trimmedValue);
    }

    // Auto-derive the name from the fetched title (URL) or file name (PDF)
    const trimmedName =
      sourceType === "url"
        ? name.trim() || trimmedValue
        : selectedFileName?.replace(/\.[^.]+$/, "") || "Untitled source";

    if (sourceType === "pdf" && !selectedFile) {
      toast.error("Choose a PDF file before submitting.");
      return;
    }

    if (sourceType === "url" && !trimmedValue) {
      toast.error("Enter a URL before submitting.");
      return;
    }

    const payload = {
      project: project.slug,
      name: trimmedName,
      type: sourceType,
      source: sourceType === "url" ? trimmedValue : undefined,
      file_name: sourceType === "pdf" ? selectedFileName : undefined,
    };

    let response;
    try {
      response = await fetch(`${backendUrl}/uploads`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
    } catch {
      const hint =
        sourceType === "url"
          ? `Make sure the backend is running at ${backendUrl} and the URL is reachable.`
          : `Make sure the backend is running at ${backendUrl}.`;
      toast.error("Could not reach the backend", {
        description: hint,
      });
      return;
    }

    if (!response.ok) {
      toast.error("Failed to add source", {
        description: response.statusText,
      });
      return;
    }

    let result;
    try {
      result = await response.json();
    } catch {
      toast.error("Invalid response from backend");
      return;
    }

    if (selectedFile) {
      const formData = new FormData();
      formData.append("file", selectedFile, selectedFile.name);

      let uploadResponse;
      try {
        uploadResponse = await fetch(
          `${backendUrl}/uploads/${result.source.id}/upload`,
          {
            method: "POST",
            body: formData,
          },
        );
      } catch {
        toast.error("Could not upload PDF", {
          description: `Make sure the backend is running at ${backendUrl}.`,
        });
        return;
      }

      if (!uploadResponse.ok) {
        const errorText = await uploadResponse.text();
        toast.error("Failed to upload PDF", {
          description: `${uploadResponse.status} ${errorText}`,
        });
        return;
      }
    }

    setSources((current) => [result.source, ...current]);
    setName("");
    setSourceValue("");
    setSelectedFile(null);
    setSelectedFileName("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    toast.success(
      sourceType === "pdf"
        ? `${trimmedName} was queued and uploaded to R2.`
        : `${trimmedName} was queued for ingestion.`,
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-16 lg:px-8">
      <div className="flex flex-col gap-4 border-b border-border pb-8 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <Badge variant="secondary" className="mb-4 w-fit">
            Project Admin
          </Badge>
          <h1 className="text-4xl font-bold tracking-tight">{project.name}</h1>
          <p className="mt-3 max-w-2xl text-lg text-muted-foreground">
            {project.description}
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link href="/projects">
            <Button variant="outline">Back to Projects</Button>
          </Link>
          <Button>
            <RefreshCw className="mr-2 h-4 w-4" />
            Sync Sources
          </Button>
        </div>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle>Project Stats</CardTitle>
            <CardDescription>
              Source coverage and ingestion summary.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <StatRow label="Sources" value={String(sources.length)} />
            <StatRow label="Processed" value={String(totals.processed)} />
            <StatRow label="Queued" value={String(totals.queued)} />
            <StatRow label="Failed" value={String(totals.failed)} />
            <StatRow label="Cancelled" value={String(totals.cancelled)} />
            <StatRow label="Chunks" value={String(totals.totalChunks)} />
          </CardContent>
        </Card>

        <Card className="border-border/50 lg:col-span-2">
          <CardHeader>
            <CardTitle>Add Source</CardTitle>
            <CardDescription>
              Add a PDF or a URL directly to the backend ingestion workflow.
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
                  <FileText className="mr-2 h-4 w-4" />
                  PDF
                </Button>
                <Button
                  type="button"
                  variant={sourceType === "url" ? "default" : "outline"}
                  onClick={() => setSourceType("url")}
                >
                  <Globe className="mr-2 h-4 w-4" />
                  URL
                </Button>
              </div>

              {sourceType === "pdf" ? (
                <div className="grid gap-2">
                  <label htmlFor="source-file" className="text-sm font-medium">
                    PDF file
                  </label>
                  <input
                    id="source-file"
                    type="file"
                    accept="application/pdf"
                    ref={fileInputRef}
                    onChange={(event) => {
                      const file = event.target.files?.[0] ?? null;
                      setSelectedFile(file);
                      setSelectedFileName(file?.name ?? "");
                    }}
                    data-slot="input"
                    className="h-8 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1 text-base transition-colors outline-none file:inline-flex file:h-6 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-input/50 disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 md:text-sm dark:bg-input/30 dark:disabled:bg-input/80 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40"
                  />
                  <p className="text-xs text-muted-foreground">
                    The browser uploads the PDF directly to R2 after the backend
                    creates the source and returns the signed URL.
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
                    The backend will fetch and ingest this URL.
                  </p>
                </div>
              )}

              <div className="flex flex-wrap gap-3">
                <Button type="submit">
                  <FileUp className="mr-2 h-4 w-4" />
                  Add Source
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setName("");
                    setSourceValue("");
                    setSelectedFileName("");
                  }}
                >
                  Reset
                </Button>
              </div>

              <p className="text-xs text-muted-foreground">
                Source metadata will later be stored in managed Postgres, while
                embeddings go to Pinecone.
              </p>
            </form>
          </CardContent>
        </Card>
      </div>

      <div className="mt-16">
        <CardHeader>
          <div className="flex items-center justify-between  border-b-3 border-border/50 px-4 py-2">
            <div className="space-y-1 mb-2">
              <CardTitle className="text-2xl font-bold">Sources</CardTitle>
              <CardDescription>
                Track what has been added, processed, and chunked.
              </CardDescription>
            </div>
            <div className="flex items-center gap-3">
              {hasActiveSources && (
                <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-amber-500" />
                  Auto-refreshing
                </span>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={fetchSources}
                disabled={hasActiveSources}
              >
                {hasActiveSources ? (
                  <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                ) : (
                  <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
                )}
                {hasActiveSources ? "Auto..." : "Refresh"}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="overflow-hidden rounded-lg border border-border/60">
            <div className="grid grid-cols-8 gap-4 border-b border-border bg-muted/40 px-4 py-3 text-sm font-medium">
              <span className="col-span-2">Source</span>
              <span>Type</span>
              <span>Status</span>
              <span>Added</span>
              <span>Size</span>
              <span>Chunks</span>
              <span>Actions</span>
            </div>
            <div className="divide-y divide-border">
              {sources.map((source) => (
                <div
                  key={source.id}
                  className="grid grid-cols-8 gap-4 px-4 py-4 text-sm items-center"
                >
                  <div className="col-span-2">
                    <p className="font-medium">{source.name}</p>
                    <p className="text-muted-foreground truncate flex items-center gap-1">
                      {source.type === "pdf" ? (
                        <FileText className="h-3 w-3 shrink-0" />
                      ) : (
                        <Globe className="h-3 w-3 shrink-0" />
                      )}
                      {source.source}
                    </p>
                  </div>
                  <div className="capitalize text-muted-foreground flex items-center gap-1">
                    {source.type === "pdf" ? (
                      <FileText className="h-3.5 w-3.5" />
                    ) : (
                      <Globe className="h-3.5 w-3.5" />
                    )}
                    {source.type}
                  </div>
                  <div>
                    <Badge variant={badgeVariantForStatus(source.status)}>
                      {source.status}
                    </Badge>
                  </div>
                  <div className="text-muted-foreground">{source.addedAt}</div>
                  <div className="text-muted-foreground">{source.size}</div>
                  <div className="text-muted-foreground">{source.chunks}</div>
                  <div className="flex gap-2">
                    {(source.status === "queued" ||
                      source.status === "processing") && (
                      <Button
                        variant="outline"
                        size="xs"
                        disabled={actionLoading === source.id}
                        onClick={() => handleCancel(source.id, source.name)}
                      >
                        {actionLoading === source.id ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <XCircle className="h-3.5 w-3.5" />
                        )}
                        <span className="ml-1.5">Cancel</span>
                      </Button>
                    )}
                    <Button
                      variant="destructive"
                      size="xs"
                      disabled={actionLoading === source.id}
                      onClick={() => handleDelete(source.id, source.name)}
                    >
                      {actionLoading === source.id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Trash2 className="h-3.5 w-3.5" />
                      )}
                      <span className="ml-1.5">Delete</span>
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
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
  if (status === "cancelled") return "outline";
  return "secondary";
}
