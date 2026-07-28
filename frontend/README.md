# Frontend

Next.js frontend for the vector search SaaS demo.

## What this folder is for

This folder holds the user interface and project admin views. If you are new to Next.js, think of it as:

- `app/` = pages and routes
- `components/` = reusable UI pieces
- `lib/` = data access and shared helpers
- `prisma/` = the Prisma schema for the shared Neon database

## Step-by-step setup

### 1) Make sure Node.js is installed

Run:

```bash
node --version
```

### 2) Install dependencies

From inside `frontend`:

```bash
npm install
```

### 3) Generate the Prisma client

The frontend reads the shared Neon connection string from `backend/.env` during local development.

If you need to regenerate the client manually, run:

```bash
npm run db:generate
```

If you need to sync the schema, run:

```bash
npm run db:push
```

### 4) Run the app

Start Next.js:

```bash
npm run dev
```

### 5) Open the main pages

Visit:

- `http://127.0.0.1:3000/`
- `http://127.0.0.1:3000/projects`
- `http://127.0.0.1:3000/admin`

## File map

### `app/page.tsx`

Landing page and product overview — hero section, core capabilities cards, architecture diagram.

### `app/projects/page.tsx`

Project directory — fetches all projects from the backend API, links to project search and admin.

### `app/projects/[slug]/page.tsx`

Per-project search page — server component that renders `SearchLayout` with hybrid search, score badges, loading skeletons, and empty states.

### `app/admin/page.tsx`

Admin dashboard — lists all projects with links to per-project admin panels.

### `app/admin/projects/[slug]/page.tsx`

Per-project admin page — server component that renders `ProjectAdminPanel`.

### `components/search-layout.tsx`

Search UI — search form with hybrid toggle, loading skeletons, result cards with source badges and scores, empty states.

### `components/project-admin-panel.tsx`

Admin panel — project stats card, add-source form (PDF upload / URL input with notes), sources table with status badges, cancel/delete actions, auto-polling every 5s for active sources.

### `components/site-shell.tsx`

App shell — sticky header with navigation (Home, Projects, Admin), mobile hamburger menu, footer.

### `components/ui/`

shadcn/ui primitives — `badge.tsx`, `button.tsx`, `card.tsx`, `input.tsx`.

### `lib/prisma.ts`

Creates the Prisma client for the frontend using the Neon adapter.

### `lib/projects.ts`

Fetches project and source metadata from the backend API — `getProjects()`, `getProjectBySlug()`.

### `lib/env.ts`

Loads the backend `.env` file so the frontend Prisma client can read `NEON_CONNECTION_STRING`.

### `prisma/schema.prisma`

Shared database schema — 4 models: Project, Source, Chunk, IngestionRun.

### `prisma.config.ts`

Prisma CLI config — reads the shared Neon database URL from `backend/.env` for frontend CLI commands.

## Environment variables

- `NEON_CONNECTION_STRING` — Neon PostgreSQL connection string (loaded from `backend/.env`)

