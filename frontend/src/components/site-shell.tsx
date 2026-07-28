"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { BowArrow } from "lucide-react";

const navLinks = [
  { href: "/", label: "Home" },
  { href: "/projects/motor-vehicle-rules", label: "Demo" },
  { href: "/docs", label: "Docs" },
];

const footerLinks = [
  { href: "/", label: "Home" },
  { href: "/docs", label: "Docs" },
  { href: "/admin", label: "Admin" },
];

export function SiteShell({ children }: { children: React.ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="min-h-full flex flex-col">
      <header className="sticky top-0 z-50 border-b border-border/70 bg-background/95 backdrop-blur-xl shadow-sm shadow-black/5">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4 sm:px-8">
          <Link
            href="/"
            className="text-lg font-semibold tracking-tight transition hover:text-primary"
          >
            <BowArrow className="inline-block mr-2 h-5 w-5" />
            Vector Search
          </Link>

          <nav className="hidden items-center gap-6 md:flex">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-sm font-medium text-muted-foreground transition hover:text-foreground"
              >
                {link.label}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <Link href="/admin" className="hidden md:inline-flex">
              <Button size="sm">Admin</Button>
            </Link>
            <button
              type="button"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((value) => !value)}
              className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-background text-muted-foreground transition hover:border-primary hover:text-foreground md:hidden"
            >
              <span className="sr-only">Toggle navigation</span>
              <svg
                viewBox="0 0 24 24"
                fill="none"
                className="h-5 w-5"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                {menuOpen ? (
                  <path d="M18 6 6 18M6 6l12 12" />
                ) : (
                  <>
                    <path d="M4 7h16" />
                    <path d="M4 12h16" />
                    <path d="M4 17h16" />
                  </>
                )}
              </svg>
            </button>
          </div>
        </div>

        <div
          className={cn(
            "md:hidden overflow-hidden transition-all duration-300",
            menuOpen ? "max-h-80" : "max-h-0",
          )}
        >
          <nav className="mx-auto max-w-6xl px-6 pb-4 sm:px-8">
            <div className="space-y-3 rounded-3xl border border-border/70 bg-card p-4 shadow-xl shadow-black/5">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="block rounded-xl px-4 py-3 text-sm font-medium text-muted-foreground transition hover:bg-muted hover:text-foreground"
                  onClick={() => setMenuOpen(false)}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </nav>
        </div>
      </header>

      <main className="flex-1 min-h-[80vh]">{children}</main>

      <footer className="border-t border-border bg-muted/50 text-sm text-muted-foreground">
        <div className="mx-auto flex max-w-6xl flex-col gap-6 px-6 py-8 sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <div className="space-y-2">
            <Link
              href="/"
              className="text-lg font-semibold tracking-tight transition hover:text-primary"
            >
              <BowArrow className="inline-block mr-2 h-5 w-5" />
              Vector Search
            </Link>
            <p className="max-w-sm leading-5 pt-2 text-xs text-neutral-400 ">
              A lightweight platform for searching and exploring domain-specific
              knowledge with citations and observability.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            {footerLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="transition hover:text-foreground"
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
