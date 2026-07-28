import { getProjects } from "@/lib/projects";

export const dynamic = "force-dynamic";

export default async function ProjectsPage() {
  const projects = await getProjects();

  return (
    <div className="mx-auto max-w-6xl px-6 py-24 sm:py-32 lg:px-8">
      <div className="mx-auto max-w-2xl text-center">
        <h1 className="text-4xl font-bold tracking-tight">Projects</h1>
        <p className="mt-4 text-lg text-muted-foreground">
          Browse and manage each searchable knowledge workspace.
        </p>
      </div>
      <div className="mt-16 grid gap-6 sm:grid-cols-2">
        {projects.map((project) => (
          <div
            key={project.slug}
            className="rounded-xl border border-border/50 bg-card p-6 shadow-sm transition-colors hover:border-border"
          >
            <div className="mb-4 flex items-center justify-between gap-3">
              <span className="rounded-full border border-border px-3 py-1 text-xs font-medium text-muted-foreground">
                {project.status}
              </span>
              <span className="text-xs text-muted-foreground">
                {project.sources.length} sources
              </span>
            </div>
            <h2 className="text-2xl font-semibold">{project.name}</h2>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">
              {project.description}
            </p>
            <div className="mt-6 flex gap-3">
              <a
                href={`/projects/${project.slug}`}
                className="inline-flex h-9 items-center justify-center rounded-md border border-input px-3 text-sm font-medium hover:bg-muted"
              >
                Open Project
              </a>
              <a
                href={`/admin/projects/${project.slug}`}
                className="inline-flex h-9 items-center justify-center rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground hover:bg-primary/80"
              >
                Manage Sources
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
