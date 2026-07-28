import "server-only";

export type SourceTypeLabel = "pdf" | "url";
export type SourceStatusLabel = "processed" | "processing" | "queued" | "failed";

export interface ProjectSource {
  id: string;
  name: string;
  type: SourceTypeLabel;
  source: string;
  addedAt: string;
  size: string;
  chunks: number;
  status: SourceStatusLabel;
  lastSynced: string;
}

export interface ProjectRecord {
  slug: string;
  name: string;
  description: string;
  status: string;
  sources: ProjectSource[];
}

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export async function getProjects(): Promise<ProjectRecord[]> {
  const response = await fetch(`${backendUrl}/projects`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to fetch projects: ${response.statusText}`);
  }

  const projects = await response.json();
  return projects.map(mapProject);
}

export async function getProjectBySlug(slug: string): Promise<ProjectRecord | null> {
  const response = await fetch(`${backendUrl}/projects/${encodeURIComponent(slug)}`, {
    cache: "no-store",
  });

  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Failed to fetch project: ${response.statusText}`);
  }

  const project = await response.json();
  return mapProject(project);
}

function mapProject(project: any): ProjectRecord {
  return {
    slug: project.slug,
    name: project.name,
    description: project.description,
    status: project.status,
    sources: project.sources
      .slice()
      .sort((left: any, right: any) => new Date(right.addedAt).getTime() - new Date(left.addedAt).getTime())
      .map(mapSource),
  };
}

function mapSource(source: any): ProjectSource {
  return {
    id: source.id,
    name: source.name,
    type: source.type,
    source: source.source,
    addedAt: source.addedAt,
    size: source.size,
    chunks: source.chunks,
    status: source.status,
    lastSynced: source.lastSynced,
  };
}
