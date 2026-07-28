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

Landing page and product overview.

### `app/projects/page.tsx`

Project directory, powered by Prisma data from Neon.

### `app/projects/*/admin/page.tsx`

Project-specific source management pages.

### `components/project-admin-panel.tsx`

The interactive admin scaffold for adding PDF and URL sources.

### `lib/prisma.ts`

Creates the Prisma client for the frontend using the Neon adapter.

### `lib/projects.ts`

Fetches and seeds project/source metadata for the scaffold.

### `prisma/schema.prisma`

Shared database schema for projects, sources, chunks, and ingestion runs.

### `prisma.config.ts`

This is where Prisma reads the shared Neon database URL for frontend CLI commands.

## Environment variables

- `NEON_CONNECTION_STRING`

