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

This is where the project and source API endpoints live.

### `app/api/schemas.py`

These are the request and response models used by the API.

### `app/core/config.py`

This loads environment variables.

FastAPI apps usually keep secrets and environment-specific values out of code. That is why this file reads from `.env`.



### `.env`

This file is for local secrets only. Do not commit it.

### `.env.example`

This is a safe template showing the variables the app expects.

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


