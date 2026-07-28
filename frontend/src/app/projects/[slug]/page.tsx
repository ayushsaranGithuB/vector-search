import { notFound } from "next/navigation";

import { SearchLayout } from "@/components/search-layout";
import { getProjectBySlug } from "@/lib/projects";

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
      projectName={project.name}
      projectDescription={project.description}
    />
  );
}
