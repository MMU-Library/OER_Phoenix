
# OER_Phoenix — quick, accurate docs

This repository contains a Django-based prototype platform for harvesting,
enriching and searching Open Educational Resources (OER). The project uses
Postgres (with the `vector` extension), optional AI enrichment, and a set of
harvesters (OAI‑PMH, MARCXML, CSV, API).

This README is the authoritative, up-to-date onboarding guide. If you are
evaluating or demoing the project, follow the Quick Start below.

---

## What changed from older docs

- Environment variable names in `oer_rebirth/settings.py` use `DB_NAME`,
   `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` for Django's database config.
   The database container still uses `POSTGRES_*` variables for initialization.
- Celery is configured in `.env` to use Redis by default; settings may fall
   back to other backends if not provided.
- The `docker-entrypoint.sh` will create a default superuser `admin` /
   `adminpass` if one does not already exist.

---

## Prerequisites

- Docker & Docker Compose (recommended: Docker Compose v2; use `docker compose`)
- Git
- For local non-Docker development: Python 3.12 (Docker image uses 3.12)

Optional services for advanced features:
- Redis (task broker)
- Qdrant (vector DB alternative)
- pgAdmin (DB admin UI)

---

## Quick Start (Docker)

1. Clone the repository:

```bash
git clone <repo-url>
cd OER_Rebirth
cp .env.example .env
# Edit .env as needed (see .env.example keys)
```

2. Build and start:

```bash
docker compose up --build -d
```

3. Follow logs while the containers start:

```bash
docker compose logs -f web
```

Notes:
- The `web` container's `docker-entrypoint.sh` waits for the DB, creates the
   database if missing, enables the Postgres `vector` extension, runs
   migrations, and creates a default superuser `admin`/`adminpass` if necessary.

---

## Environment variables (important)

The project uses a `.env` file. A complete example is provided in `.env.example`.
Key variables you will commonly set:

- `DJANGO_SECRET_KEY` — Django secret key.
- `DJANGO_DEBUG` — `True` / `False` for local dev vs production.

# Database
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` — used by Django.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` — used by the DB
   container during first-time initialization (these often mirror the `DB_*`
   values but are read by the Postgres image).

# Celery / Redis
- `CELERY_BROKER_URL` — e.g. `redis://redis:6379/0` (recommended when using
   the provided `redis` service in `docker-compose.yml`).
- `CELERY_RESULT_BACKEND` — e.g. `redis://redis:6379/1`.

# Local LLM / AI enrichment
- `LOCAL_LLM_URL`, `LOCAL_LLM_MODEL`, `LOCAL_LLM_TIMEOUT` — URL and model for
   any local model used for enrichment. When using Docker Desktop and running
   an LLM on the host, use `http://host.docker.internal:<port>` in the `.env`.
- `ENABLE_LLM_ENRICHMENT` — set `False` by default unless you have an LLM
   available. Installing AI deps (torch, transformers) is optional and
   recommended only for users who enable enrichment.

---

## First-run checklist (after `docker compose up`)

1. Visit: http://localhost:8000/ (admin at `/admin/`).
2. Default admin user: `admin` / `adminpass` (created by entrypoint if missing).
    Please change the password immediately.
3. Add an OER source in the admin and run a harvest (see management commands).

---

## Management commands (run inside the `web` container)

Open a shell in the web container:

```bash
docker compose exec web bash
```

Common commands (exact names present under `resources/management/commands`):

- `python manage.py fetch_oer` — run harvests (see command help for args).
- `python manage.py normalise_resource_type` — normalise legacy resource types.
- `python manage.py enrich_subjects` — run subject enrichment/backfill jobs.
- `python manage.py export_talis` — export resources to Talis (requires creds).
- `python manage.py reindex_qdrant` — reindex into Qdrant (if used).
- `python manage.py apply_subject_itemtypes` — apply item type mappings.
- `python manage.py backfill_subjects` — backfill subject data.

Use `python manage.py help <command>` to view usage for each command.

---

## Celery / background tasks

The Compose file includes `celery` and `celery-beat` services. Ensure
`CELERY_BROKER_URL` in `.env` points to Redis when using the bundled Redis
service. Example values are present in `.env.example`.

---

## Optional services

- Qdrant: exposed on port `6333` in `docker-compose.yml` when enabled.
- pgAdmin: exposed on port `8080` (useful for inspecting the Postgres DB).

---

## Troubleshooting

- Database connection errors: verify `.env` DB_* values and that the `db`
   container is healthy (`docker compose ps` / `docker compose logs db`).
- Celery not processing tasks: check `docker compose logs celery` and ensure
   `CELERY_BROKER_URL` points to a running Redis instance.
- Embeddings or AI jobs failing: ensure `ENABLE_LLM_ENRICHMENT=true` and
   `LOCAL_LLM_URL` points to a reachable model; install optional AI packages
   only when required.

---

## Contributing

- Fork, branch, and open a pull request to `main`. Keep documentation changes
   in the same PR as related code changes.

---

If you want, I can now apply these documentation changes to `OldREADME.md`
and create a short `.env.example` if you prefer a trimmed version. I will not
change any runtime code in this step.


