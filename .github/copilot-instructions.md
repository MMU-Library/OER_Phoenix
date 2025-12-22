## Quick Orientation for AI coding agents

This file provides concise, actionable guidance to help an AI agent be productive in this repository.

**Project summary:** Django-based OER harvesting/enrichment/search prototype. Core pieces:
- `oer_rebirth/` — Django project entry (settings, wsgi, asgi, celery).
- `resources/` — main app: models, management commands, harvesters, Celery tasks, and views.
- `resources/harvesters/` — harvester implementations (OAI‑PMH, MARCXML, CSV, API).
- `services/` — enrichment, AI client, search & quality logic (LLM integration lives here).
- `scripts/` — one-off CLI runner scripts for harvest/testing.

**Architecture & data flow (short):**
- Harvesters ingest external sources and create/update `resources.models.OERResource` records.
- Background work uses Celery (see `oer_rebirth/celery.py` and `resources/tasks.py`).
- Enrichment pipelines live in `services/` (e.g. `llm_client.py`, `metadata_enricher.py`).
- Search indexing can target Qdrant or Postgres vector (`services/search_engine.py`).

**Important files to inspect quickly**
- [oer_rebirth/settings.py](oer_rebirth/settings.py) — env-driven config (`DB_*`, `CELERY_BROKER_URL`, `LOCAL_LLM_*`).
- [resources/models.py](resources/models.py) — central domain model(s); `OERResource` is primary.
- [resources/management/commands](resources/management/commands/) — useful management commands (harvest, backfill, exports).
- [resources/harvesters/](resources/harvesters/) — harvester subclasses inherit `base_harvester.py`.
- [services/](services/) — AI/enrichment/search helpers and integration points.

**Conventions & patterns found in this repo**
- Management commands and scripts are the canonical ways to run harvests or backfills; prefer `python manage.py <command>` inside the `web` container or local venv.

- Docker-first: this project is developed and run inside Docker Compose in normal workflows. Prefer `docker compose exec web <command>` for `manage.py`, migrations, and running Celery workers so that service hostnames (e.g. `db`, `redis`) resolve correctly. Avoid running Django manage commands from a local venv unless you have a local Postgres/Redis matching the `.env` settings.
- Harvesters follow a common base class pattern (`base_harvester.py`) and use helper functions in `harvesters/utils.py` and `preset_configs.py` for source configuration.
- Celery tasks are defined in `resources/tasks.py`; periodic scheduling is driven by `celery-beat` when enabled.
- AI enrichment is optional and guarded by environment variables: `ENABLE_LLM_ENRICHMENT`, `LOCAL_LLM_URL`, `LOCAL_LLM_MODEL`.

**Run & debug tips (examples)**
- Start full stack (recommended): `docker compose up --build -d` then `docker compose logs -f web`.
- Inside the web container, run migrations / commands:
  - `docker compose exec web bash`
  - `python manage.py migrate`
  - `python manage.py help fetch_oer` (see available management commands in `resources/management/commands`).
- Run Celery locally: `celery -A oer_rebirth worker -l info` and `celery -A oer_rebirth beat -l info` (ensure `CELERY_BROKER_URL` points to Redis).

**Tests & validation**
- Tests live under `resources/tests/` (e.g. `test_api_search.py`, `test_harvesters.py`). Use `python manage.py test` or `pytest` if available in the environment.

**Agent-focused guidance**
- When changing harvesters, update `resources/harvesters/preset_configs.py` if adding new source presets.
- Prefer altering management commands in `resources/management/commands/` for reproducible CLI workflows (these are used by CI and maintainers).
- Be conservative with DB migrations: examine `resources/migrations/` and keep migrations minimal and reversible.
- Search for usages of `OERResource` to discover side effects (signals, tasks, exports). Helpful files: `resources/signals.py`, `resources/tasks.py`, `services/talis.py`.

**Examples taken from the repo**
- The small backfill command `resources/management/commands/apply_subject_item_types.py` uses model fields like `keywords`, `format`, `level` to infer `subject` and `resource_type` — follow those field names when writing schema- or data-related code.

If anything here is unclear or you want more detail on a particular area (harvest flow, Celery setup, LLM integration), tell me which area to expand and I will iterate.
