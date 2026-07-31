import "server-only";

export interface LogEntry {
    id: string;
    timestamp: string;
    event: string;
    query: string | null;
    source_ids: string[];
    model_slug: string | null;
    input_tokens: number | null;
    output_tokens: number | null;
    cost_usd: number | null;
    latency_ms: number | null;
    error_message: string | null;
    metadata: Record<string, unknown> | null;
}

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export async function getLogs(limit = 100): Promise<LogEntry[]> {
    const response = await fetch(`${backendUrl}/logs?limit=${limit}`, {
        cache: "no-store",
    });

    if (!response.ok) {
        throw new Error(`Failed to fetch logs: ${response.statusText}`);
    }

    return response.json();
}
