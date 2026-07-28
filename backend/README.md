# Backend

FastAPI backend for the vector search SaaS demo.

## What this folder is for

This folder holds the API and backend logic. If you are new to FastAPI, think of it as:

- `main.py` = starts the app
- `api/` = groups routes by purpose
- `core/` = shared configuration and helpers
- `services/` = database and data-shaping logic
- `health.py` = a tiny first endpoint to prove the server is running

## Step-by-step setup

### 1) Make sure Python is installed

Check your version:

```bash
python --version
```

This project expects Python 3.11 or newer. You already have Python 3.13, so that part is good.

### 2) Create a virtual environment

From inside the `backend` folder:

```bash
python -m venv .venv
```

Activate it:

```bash
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again.

### 3) Install dependencies

Still inside `backend`:

```bash
pip install -e .[dev]
```

What this means:

- `pip` installs Python packages
- `-e` means editable mode, so code changes are picked up immediately
- `.[dev]` means install the project plus the optional `dev` tools from `pyproject.toml`

### 4) Sync Prisma with Neon

This backend uses Prisma Python, the shared Neon connection string stored in `backend/.env`, and `backend/prisma.config.ts` to keep the connection URL out of the schema.

If you need to sync the schema manually, run:

```bash
.\.venv\Scripts\prisma.exe db push --schema .\prisma\schema.prisma
```

If you change the schema and want to regenerate the client, run:

```bash
.\.venv\Scripts\prisma.exe generate --schema .\prisma\schema.prisma
```

### 5) Run the app

Start the server with Uvicorn:

```bash
uvicorn app.main:app --reload
```

What this means:

- `app.main` points to `backend/app/main.py`
- `app` is the FastAPI instance inside that file
- `--reload` restarts the server whenever you edit code

### 6) Open the first endpoint

Visit:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

`/docs` is the auto-generated FastAPI documentation.

### 7) Run the ingestion worker (separate terminal)

The worker processes queued ingestion tasks (PDF chunking, embedding, Pinecone upsert):

```bash
python -m app.services.worker
```

Run this in a separate terminal while the API server is running.

## File map

### `pyproject.toml`

This is the project configuration file. It tells Python:

- the package name
- the Python version required
- which libraries to install
- which dev tools to install

### `app/main.py`

This is the app entrypoint. FastAPI creates the server here.

### `app/api/router.py`

This collects smaller routers into one API router. That way routes stay organized as the app grows.

### `app/api/routes/health.py`

This contains the first route.

```py
@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

The syntax means:

- `@router.get("/health")` attaches this function to the `GET /health` path
- `def health_check()` defines a normal Python function
- `-> dict[str, str]` is a type hint that says the function returns a dictionary of strings

### `app/api/routes/projects.py`

Project and source API endpoints — list projects, get project details, list sources, search, create sources.

### `app/api/routes/sources.py`

Source management endpoints — delete and cancel sources (cascades to Pinecone vectors, R2 objects, and DB).

### `app/api/routes/uploads.py`

Upload endpoints — create upload (returns presigned URL), upload file bytes, finalize upload (triggers ingestion).

### `app/api/schemas.py`

Request and response models used by the API — `ProjectOut`, `SourceOut`, `SourceCreateInput`, `UploadCreateOut`, `SearchResultOut`, etc.

### `app/core/config.py`

Loads environment variables via Pydantic Settings. Reads from `.env` for:

- `APP_ENV`, `CORS_ORIGINS`
- `NEON_CONNECTION_STRING`
- `PINECONE_API_KEY`, `PINECONE_INDEX`, `PINECONE_CLOUD`, `PINECONE_REGION`
- `CLOUDAMQP_URL`
- `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_ACCOUNT_ID`

### `app/services/pinecone.py`

Pinecone vector DB client — lazy-init, batched embedding (`multilingual-e5-large`), upsert, query, delete.

### `app/services/ingest.py`

Document ingestion pipeline — PDF text extraction (`pypdf`), URL fetching (`httpx`), text chunking (1000 chars, 200 overlap), batch embedding + Pinecone upsert, status tracking.

### `app/services/queue.py`

CloudAMQP (RabbitMQ) publisher — enqueues ingestion tasks to the `ingestion` exchange.

### `app/services/worker.py`

Standalone async worker — connects to DB, listens on `ingestion.queue`, calls `ingest_source` for each message.

### `app/services/storage.py`

Cloudflare R2 client — S3-compatible object storage for PDFs, presigned URL generation.

### `app/services/uploads.py`

Upload orchestration — creates source records, generates presigned URLs, handles direct upload and finalization.

### `app/services/projects.py`

Project and source data access — CRUD, search with Pinecone vector + PostgreSQL keyword fallback.

### `app/services/sources.py`

Source lifecycle management — delete (cascades Pinecone → R2 → DB), cancel (QUEUED/PROCESSING → CANCELLED).

### `app/db.py`

Prisma client singleton — connects/disconnects on app lifespan.

### `.env`

Local secrets only. Do not commit it.

### `.env.example`

Safe template showing all variables the app expects.

## Beginner syntax notes

### What is a decorator?

This line:

```py
@router.get("/health")
```

is a decorator. It means: attach the function below to a route.

### What is a router?

A router is a way to group endpoints. Instead of putting every endpoint in one file, you can split them by feature.

### What is a settings class?

This part:

```py
class Settings(BaseSettings):
```

creates a class that reads values from environment variables.

### Why `lru_cache`?

This part:

```py
@lru_cache(maxsize=1)
```

means the settings object is created once and reused. That avoids re-reading config on every import.

## If install fails

Common fixes:

- make sure you are running the command from inside the `backend` folder
- make sure the virtual environment is activated
- upgrade packaging tools:

```bash
python -m pip install --upgrade pip setuptools wheel
```

- retry the install:

```bash
pip install -e .[dev]
```

## Environment variables

- `NEON_CONNECTION_STRING`
- `PINECONE_API_KEY`
- `PINECONE_INDEX`
- `PINECONE_CLOUD`
- `PINECONE_REGION`
- `APP_ENV`
- `CORS_ORIGINS`


