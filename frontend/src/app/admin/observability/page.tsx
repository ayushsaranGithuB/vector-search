import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getLogs, type LogEntry } from "@/lib/logs";

export const dynamic = "force-dynamic";

function formatLatency(ms: number | null | undefined): string {
  if (ms === null || ms === undefined) return "—";
  return `${ms}ms`;
}

function formatCost(cost: number | null | undefined): string {
  if (cost === null || cost === undefined) return "—";
  return `$${cost.toFixed(6)}`;
}

function formatTokens(tokens: number | null | undefined): string {
  if (tokens === null || tokens === undefined) return "—";
  return `${tokens}`;
}

function formatEventLabel(event: string): string {
  switch (event) {
    case "SEARCH":
      return "Search Query";
    case "LLM_CALL":
      return "LLM Call";
    case "ERROR":
      return "Error";
    default:
      return event;
  }
}

function logDetails(log: LogEntry): string {
  const parts: string[] = [];
  if (log.query) parts.push(`Query: ${log.query}`);
  if (log.model_slug) parts.push(`Model: ${log.model_slug}`);
  if (log.source_ids && log.source_ids.length > 0) {
    parts.push(`Sources: ${log.source_ids.length}`);
  }
  if (log.error_message) parts.push(`Error: ${log.error_message}`);
  return parts.join(" · ") || "No details";
}

export default async function ObservabilityPage() {
  let logs: LogEntry[] = [];
  let errorMessage: string | null = null;

  try {
    logs = await getLogs();
  } catch (error) {
    errorMessage =
      error instanceof Error ? error.message : "Unable to load logs.";
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-24 sm:py-32 lg:px-8">
      <div className="mx-auto max-w-2xl text-center">
        <Badge variant="secondary" className="mb-4 w-fit px-3 py-1 text-sm">
          Observability
        </Badge>
        <h1 className="text-4xl font-bold tracking-tight">
          Query Analytics & Logs
        </h1>
        <p className="mt-4 text-lg text-muted-foreground">
          Monitor search performance, LLM usage, and system errors.
        </p>
      </div>

      {errorMessage ? (
        <div className="mx-auto mt-16 max-w-3xl rounded-xl border border-destructive/20 bg-destructive/5 p-6 text-sm text-destructive">
          <h2 className="text-lg font-semibold text-destructive">
            Unable to load logs
          </h2>
          <p className="mt-2">{errorMessage}</p>
        </div>
      ) : (
        <div className="mt-16 grid gap-6">
          {logs.length === 0 && (
            <p className="text-center text-muted-foreground">
              No logs yet. Run a search or generate a summary to see analytics.
            </p>
          )}
          {logs.map((log) => (
            <Card key={log.id} className="border-border/50">
              <CardHeader>
                <CardTitle className="text-sm font-medium">
                  {formatEventLabel(log.event)}
                </CardTitle>
                <CardDescription>{log.timestamp}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-sm">{logDetails(log)}</p>
                <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
                  <span>Latency: {formatLatency(log.latency_ms)}</span>
                  <span>Input tokens: {formatTokens(log.input_tokens)}</span>
                  <span>Output tokens: {formatTokens(log.output_tokens)}</span>
                  <span>Cost: {formatCost(log.cost_usd)}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
