import { notFound } from "next/navigation";

import { SearchLayout } from "@/components/search-layout";
import { getProjectBySlug } from "@/lib/projects";

export const dynamic = "force-dynamic";

interface ProjectPageProps {
  params: Promise<{ slug: string }>;
}

export default async function ProjectPage({ params }: ProjectPageProps) {
  const { slug } = await params;

  const project = await getProjectBySlug(slug);

  if (!project) {
    notFound();
  }

  return (
    <SearchLayout
      projectSlug={slug}
      projectName={project.name}
      projectDescription={project.description}
    />
  );
}
