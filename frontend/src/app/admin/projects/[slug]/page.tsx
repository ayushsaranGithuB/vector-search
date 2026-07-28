import { notFound } from "next/navigation";

import { ProjectAdminPanel } from "@/components/project-admin-panel";
import { getProjectBySlug } from "@/lib/projects";

interface AdminProjectPageProps {
  params: Promise<{ slug: string }>;
}

export default async function AdminProjectPage({
  params,
}: AdminProjectPageProps) {
  const { slug } = await params;

  // REMOVED - await ensureDemoProjects(); LIVE DATA ONLY via NEONDB
  const project = await getProjectBySlug(slug);

  if (!project) {
    notFound();
  }

  return <ProjectAdminPanel project={project} />;
}
