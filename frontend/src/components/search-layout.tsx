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

interface SearchResult {
  id: string;
  title: string;
  excerpt: string;
  source: string;
  score: number;
  citation: string;
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

  async function handleSearch(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setHasSearched(true);

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
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-12 lg:px-8">
      {/* Project Header */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight">{projectName}</h1>
        <p className="mt-2 text-muted-foreground">{projectDescription}</p>
      </div>

      {/* Search Box */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search across documents..."
              className="flex h-12 w-full rounded-lg border border-input bg-background px-4 py-3 text-base ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>
          <Button
            type="submit"
            size="lg"
            disabled={isSearching || !query.trim()}
          >
            {isSearching ? "Searching..." : "Search"}
          </Button>
        </div>
      </form>

      {/* Search Mode Toggle */}
      <div className="mb-6 flex items-center gap-2 text-sm text-muted-foreground">
        <span>Search mode:</span>
        <Badge variant="secondary" className="cursor-pointer">
          Hybrid
        </Badge>
        <span className="text-xs">(keyword + vector)</span>
      </div>

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
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Found {results.length} result{results.length !== 1 ? "s" : ""}
          </p>
          {results.map((result) => (
            <Card
              key={result.id}
              className="border-border/50 transition-colors hover:border-border"
            >
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <CardTitle className="text-base">{result.title}</CardTitle>
                    <CardDescription className="mt-1">
                      Source: {result.source} &middot; Citation:{" "}
                      {result.citation}
                    </CardDescription>
                  </div>
                  <Badge variant="outline" className="shrink-0">
                    {(result.score * 100).toFixed(0)}% match
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {result.excerpt}
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
