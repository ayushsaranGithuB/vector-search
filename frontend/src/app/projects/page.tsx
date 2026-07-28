import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const projects = [
  {
    title: "Indian Motor Vehicle Rules",
    description:
      "Search and retrieve information from Indian motor vehicle regulations and traffic laws with grounded citations.",
    href: "/projects/motor-vehicle-rules",
    status: "Coming Soon" as const,
  },
  {
    title: "Domain Knowledge Base",
    description:
      "A second domain-specific knowledge project demonstrating the platform's reusability across different contexts.",
    href: "/projects/domain-knowledge-base",
    status: "Coming Soon" as const,
  },
];

export default function ProjectsPage() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-24 sm:py-32 lg:px-8">
      <div className="mx-auto max-w-2xl text-center">
        <h1 className="text-4xl font-bold tracking-tight">Projects</h1>
        <p className="mt-4 text-lg text-muted-foreground">
          Browse and search across knowledge domains.
        </p>
      </div>
      <div className="mt-16 grid gap-6 sm:grid-cols-2">
        {projects.map((project) => (
          <Card
            key={project.title}
            className="border-border/50 transition-colors hover:border-border"
          >
            <CardHeader>
              <Badge className="mb-2 w-fit">{project.status}</Badge>
              <CardTitle>{project.title}</CardTitle>
              <CardDescription>{project.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <Link href={project.href}>
                <Button variant="outline" size="sm" disabled={project.status === "Coming Soon"}>
                  Open Project
                </Button>
              </Link>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}