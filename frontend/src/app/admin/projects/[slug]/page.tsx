import { notFound } from "next/navigation";

import { ProjectAdminPanel } from "@/components/project-admin-panel";
import { getProjectBySlug } from "@/lib/projects";

export const dynamic = "force-dynamic";

interface AdminProjectPageProps {
  params: Promise<{ slug: string }>;
}

export default async function AdminProjectPage({
  params,
}: AdminProjectPageProps) {
  const { slug } = await params;
  let project = null;
  let errorMessage: string | null = null;

  try {
    project = await getProjectBySlug(slug);
  } catch (error) {
    errorMessage =
      error instanceof Error ? error.message : "Unable to load project.";
  }

  if (errorMessage) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-24 sm:py-32 lg:px-8">
        <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-6 text-sm text-destructive">
          <h1 className="text-2xl font-semibold">Unable to load project</h1>
          <p className="mt-2">{errorMessage}</p>
          <p className="mt-2 text-muted-foreground">
            Check backend connectivity and try again.
          </p>
        </div>
      </div>
    );
  }

  if (!project) {
    notFound();
  }

  return <ProjectAdminPanel project={project} />;
}
