"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Image from "next/image";
import { LoaderCircle, Send } from "lucide-react";

interface SearchResult {
  id: string;
  title: string;
  excerpt: string;
  source: string;
  source_url: string | null;
  score: number;
  citation: string;
}

interface SearchSummary {
  summary: string;
  generated_from: number;
  model_slug: string;
  model_label: string;
}

interface SearchLayoutProps {
  projectSlug: string;
  projectName: string;
  projectDescription: string;
}

const backendUrl =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export function SearchLayout({
  projectSlug,
  projectName,
  projectDescription,
}: SearchLayoutProps) {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [summary, setSummary] = useState<SearchSummary | null>(null);
  const [isSummarizing, setIsSummarizing] = useState(false);

  /** Highlight matching terms in text */
  function highlightMatches(
    text: string,
    searchQuery: string,
  ): React.ReactNode {
    if (!searchQuery.trim()) return text;

    const terms = searchQuery
      .trim()
      .split(/\s+/)
      .filter((t) => t.length > 0)
      .map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));

    if (terms.length === 0) return text;

    const pattern = `(${terms.join("|")})`;
    const regex = new RegExp(pattern, "gi");
    const parts = text.split(regex);

    return parts.map((part, i) => {
      if (!part) return null;
      const isMatch = new RegExp(`^${pattern}$`, "i").test(part);
      return isMatch ? (
        <mark
          key={i}
          className="rounded-sm bg-yellow-200 px-0.5 text-inherit dark:bg-yellow-700/60"
        >
          {part}
        </mark>
      ) : (
        part
      );
    });
  }

  async function handleSearch(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setHasSearched(true);
    setSummary(null);

    const response = await fetch(
      `${backendUrl}/projects/${encodeURIComponent(
        projectSlug,
      )}/search?q=${encodeURIComponent(query)}`,
    );

    if (!response.ok) {
      setResults([]);
      setIsSearching(false);
      return;
    }

    const data = await response.json();
    setResults(data);
    setIsSearching(false);

    // Auto-generate AI summary
    if (data.length > 0) {
      setIsSummarizing(true);
      try {
        const summaryResponse = await fetch(
          `${backendUrl}/projects/${encodeURIComponent(
            projectSlug,
          )}/search/summary?q=${encodeURIComponent(query)}`,
        );
        if (summaryResponse.ok) {
          const summaryData: SearchSummary = await summaryResponse.json();
          setSummary(summaryData);
        }
      } catch (err) {
        console.error("Summary generation error:", err);
      } finally {
        setIsSummarizing(false);
      }
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-12 lg:px-8">
      {/* Project Header */}
      <div className="mb-8 text-center flex flex-col items-center gap-2">
        <Image src={"/images/car.svg"} width={60} height={60} alt="car icon" />
        <h1 className="text-xl font-bold tracking-tight">{projectName}</h1>
        <p className="mt-2 text-muted-foreground text-sm">
          {projectDescription}
        </p>
      </div>

      {/* Search Box */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex gap-3">
          <div className="relative flex-1 rounded-lg border border-input bg-background px-4 py-3 pb-12 ">
            <textarea
              name="searchQuery"
              value={query}
              rows={2}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSearch(e);
                }
              }}
              placeholder="Ask a question or search across official documents..."
              className="flex w-full  text-base ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none  disabled:cursor-not-allowed disabled:opacity-50 placeholder:text-neutral-400 field-sizing-content resize-none"
            />
            <Button
              type="submit"
              size="lg"
              disabled={isSearching || !query.trim()}
              className={"absolute bottom-2 right-2"}
            >
              {isSearching ? (
                <LoaderCircle className="animateRotate" />
              ) : (
                <Send />
              )}
            </Button>
          </div>
        </div>
      </form>

      {/* Search Mode Toggle */}
      {/* <div className="mb-6 flex items-center gap-2 text-sm text-muted-foreground">
        <span>Search mode:</span>
        <Badge variant="secondary" className="cursor-pointer">
          Hybrid
        </Badge>
        <span className="text-xs">(keyword + vector)</span>
      </div> */}

      {/* Results Area */}
      {isSearching && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse border-border/50">
              <CardHeader>
                <div className="h-5 w-48 rounded bg-muted" />
                <div className="mt-2 h-3 w-32 rounded bg-muted" />
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="h-3 w-full rounded bg-muted" />
                  <div className="h-3 w-5/6 rounded bg-muted" />
                  <div className="h-3 w-4/6 rounded bg-muted" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {!isSearching && hasSearched && results.length === 0 && (
        <div className="py-16 text-center">
          <p className="text-lg text-muted-foreground">No results found.</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Try adjusting your search query.
          </p>
        </div>
      )}

      {!isSearching && results.length > 0 && (
        <div className="space-y-6">
          {/* Result Count */}
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Found {results.length} result{results.length !== 1 ? "s" : ""}
            </p>
          </div>

          {/* AI Summary */}
          {isSummarizing && (
            <Card className="border-primary/20 bg-primary/5">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">AI Summary</CardTitle>
                <CardDescription className="text-xs">
                  Generating...
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="animate-pulse space-y-2">
                  <div className="h-3 w-full rounded bg-muted" />
                  <div className="h-3 w-5/6 rounded bg-muted" />
                  <div className="h-3 w-4/6 rounded bg-muted" />
                </div>
              </CardContent>
            </Card>
          )}

          {summary && !isSummarizing && (
            <Card className="border-primary/20 bg-primary/5">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-sm">AI Summary</CardTitle>
                    <CardDescription className="text-xs">
                      {summary.model_label} &middot; {summary.generated_from}{" "}
                      results
                    </CardDescription>
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {summary.model_slug}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none text-muted-foreground [&_p]:mb-3 [&_p:last-child]:mb-0">
                  {summary.summary.split("\n\n").map((paragraph, i) => {
                    const withCitations = paragraph.replace(
                      /\[(\d+)\]/g,
                      (match, num) => {
                        const idx = parseInt(num, 10) - 1;
                        if (idx >= 0 && idx < results.length) {
                          const r = results[idx];
                          const href = r.source_url ?? `#result-${r.id}`;
                          const target = r.source_url ? "_blank" : "";
                          const rel = r.source_url ? "noopener noreferrer" : "";
                          return (
                            `<a href="${href}" target="${target}" rel="${rel}" class="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary no-underline hover:bg-primary/20">` +
                            match +
                            ` ${r.source}</a>`
                          );
                        }
                        return match;
                      },
                    );
                    return (
                      <p
                        key={i}
                        dangerouslySetInnerHTML={{
                          __html: withCitations,
                        }}
                      />
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          <h2 className="text-lg font-semibold pt-16">Sources:</h2>

          {/* Result Cards */}
          {results.map((result, index) => (
            <Card
              key={result.id}
              id={`result-${result.id}`}
              className="border-border/50 transition-colors hover:border-border"
            >
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <CardTitle className="text-base">
                      <span className="text-xs font-normal text-muted-foreground mr-1">
                        [{index + 1}]
                      </span>
                      {highlightMatches(result.title, query)}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      Source:{" "}
                      {result.source_url ? (
                        <a
                          href={result.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-medium text-primary underline-offset-2 hover:underline"
                        >
                          {result.source}
                        </a>
                      ) : (
                        result.source
                      )}{" "}
                      &middot; Citation: {result.citation}
                    </CardDescription>
                  </div>
                  <Badge variant="outline" className="shrink-0">
                    {(result.score * 100).toFixed(0)}% match
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {highlightMatches(result.excerpt, query)}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!hasSearched && (
        <div className="py-16 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <svg
              className="h-6 w-6 text-muted-foreground"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"
              />
            </svg>
          </div>
          <p className="text-lg text-muted-foreground">
            Ask a question or search across documents
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            Results will appear here with citations and relevance scores.
          </p>
        </div>
      )}
    </div>
  );
}
