import Link from "next/link";
import { Button } from "@/components/ui/button";
import { SearchLayout } from "@/components/search-layout";
import { getProjectBySlug } from "@/lib/projects";

export default async function Home() {
  const project = await getProjectBySlug("motor-vehicle-rules");

  return (
    <>
      {/* Hero Section */}
      <section className="relative overflow-hidden ">
        <div className="relative mx-auto max-w-6xl px-6 pt-34 pb-0  lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-3xl font-bold tracking-tight sm:text-7xl">
              Vector Search
            </h1>
            <p className="mt-6 text-lg leading-8 text-muted-foreground">
              An AI search platform for multiple projects and datasets, built to
              show grounded retrieval, citations, and observability in one
              reusable system.
            </p>
            <div className="mt-4 flex items-center justify-center gap-4">
              <Link href="/docs">
                <Button
                  size="sm"
                  variant="outline"
                  className=" px-4 py-3 h-auto rounded-full text-xs tracking-wider text-neutral-500"
                >
                  Read the Docs
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Search Section */}
      <section>
        {project ? (
          <SearchLayout
            projectSlug={project.slug}
            projectName={project.name}
            projectDescription={project.description}
          />
        ) : (
          <div className="mx-auto max-w-4xl px-6 py-24 text-center">
            <p className="text-lg text-muted-foreground">
              Project not found. Check the slug or add a project.
            </p>
          </div>
        )}
      </section>
    </>
  );
}
