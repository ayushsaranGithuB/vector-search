import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getProjects } from "@/lib/projects";

export const dynamic = "force-dynamic";

export default async function AdminPage() {
  let projects: Awaited<ReturnType<typeof getProjects>> = [];
  let errorMessage: string | null = null;

  try {
    projects = await getProjects();
  } catch (error) {
    errorMessage =
      error instanceof Error ? error.message : "Unable to load projects.";
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-24 sm:py-32 lg:px-8">
      <div className="mx-auto max-w-2xl text-center">
        <Badge variant="secondary" className="mb-4 w-fit px-3 py-1 text-sm">
          Admin Dashboard
        </Badge>
        <h1 className="text-4xl font-bold tracking-tight">
          Global Admin Panel
        </h1>
        <p className="mt-4 text-lg text-muted-foreground">
          Manage projects, sources, and ingestion workflows from one central
          admin view.
        </p>
      </div>

      {errorMessage ? (
        <div className="mx-auto max-w-3xl rounded-xl border border-destructive/20 bg-destructive/5 p-6 text-sm text-destructive">
          <h2 className="text-lg font-semibold text-destructive">
            Unable to load projects
          </h2>
          <p className="mt-2">{errorMessage}</p>
          <p className="mt-2 text-muted-foreground">
            Check that the backend is running and the API URL is configured
            correctly.
          </p>
        </div>
      ) : (
        <div className="mt-16 grid gap-6 sm:grid-cols-2">
          {projects.map((project) => (
            <Card
              key={project.slug}
              className="border-border/50 transition-colors hover:border-border"
            >
              <CardHeader>
                <Badge className="mb-2 w-fit">{project.status}</Badge>
                <CardTitle>{project.name}</CardTitle>
                <CardDescription>{project.description}</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                <p className="text-sm text-muted-foreground">
                  {project.sources.length} sources, ready for ingestion and
                  retrieval.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Link href={`/projects/${project.slug}`}>
                    <Button variant="outline" size="sm">
                      View Project
                    </Button>
                  </Link>
                  <Link href={`/admin/projects/${project.slug}`}>
                    <Button size="sm">Open Admin</Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
