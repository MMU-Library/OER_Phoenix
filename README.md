
# OER_Phoenix

OER_Phoenix is an open‑source discovery and analysis platform for Open Educational Resources (OER), developed at Manchester Metropolitan University Library Services. It aggregates OER from multiple providers (e.g. OAPEN, DOAB, OER Commons, Skills Commons) and provides AI‑supported search, faceting, and enrichment to support librarians, academics, and students.

---

## Key features

- Hybrid search: keyword + embedding‑based ranking, with “Why this result?” diagnostics.
- Rich filters: source, language, resource type (book/chapter/article/video/course), licence, subject area.
- Multiple harvesters: API, OAI‑PMH, CSV, and MARCXML, with normalised language and type handling.
- Talis Reading Lists support: analysis of lists vs available OER, and optional push‑back of matches.
- AI enrichment: optional embeddings, summaries, and (planned) AI‑assisted subject grouping.

---

## Repository layout (selected)

```
oer_rebirth/
├── oer_rebirth/
│   ├── settings.py          # Django settings, env loading, pgvector config
│   └── urls.py
├── resources/
│   ├── models.py            # OERSource, OERResource, HarvestJob, TalisPushJob
│   ├── views.py             # Dashboard, AI search, advanced search, Talis flows, exports
│   ├── services/
│   │   ├── search_engine.py     # Hybrid search & facets
│   │   ├── talis.py             # Talis CSV/URL parsing
│   │   └── talis_analysis.py    # Per‑item OER matching & coverage
│   ├── harvesters/             # API, OAI-PMH, CSV, MARCXML harvesters
│   ├── management/commands/    # Harvesting, type normalisation, enrichment
│   ├── templatetags/
│   │   └── oer_filters.py       # Badges, scores, link‑type logic
│   └── templates/resources/
│       ├── dashboard.html
│       ├── search.html          # AI search
│       ├── advanced_search.html
│       ├── compare.html
│       ├── export.html
│       ├── talis_*.html
│       └── partials/
├── docker-compose.yml
├── docker-compose.override.yml
├── docker-entrypoint.sh
└── README.md
```

---

## Running with Docker

### 1. Clone and configure

```
git clone https://github.com/MMU-Library/OER_Phoenix.git
cd OER_Phoenix
cp .env.example .env  # if present; otherwise create .env
```

Set at least in `.env` (local development defaults):

```
DJANGO_SECRET_KEY=change-me-to-a-long-random-string
POSTGRES_DB=oer_rebirth
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Optional but recommended for local enrichment
LOCAL_LLM_URL=http://host.docker.internal:11434/v1/chat
LOCAL_LLM_MODEL=llama3.1
LOCAL_LLM_TIMEOUT=30
ENABLE_LLM_ENRICHMENT=false  # set true once you have a model running
```

If you intend to use the Talis integration, also configure:

```
TALIS_API_URL=...
TALIS_CLIENT_ID=...
TALIS_CLIENT_SECRET=...
```

(See `resources/services/talis.py` for expected usage.)

### 2. Build and start containers

```
docker compose build
docker compose up -d
```

The `web` container’s `docker-entrypoint.sh` will:

- Wait for Postgres (`pg_isready`).
- Ensure the database exists and enable the `vector` extension.
- Run `makemigrations` and `migrate`.
- Create a default superuser (`admin` / `adminpass`) if one does not already exist.

You can follow progress with:

```
docker compose logs -f web
```

### 3. First run checklist

1. Visit the site:
   - Dashboard & AI Search: <http://localhost:8000/>
   - Advanced Search: <http://localhost:8000/advanced-search/>
   - Admin: <http://localhost:8000/admin/>

2. Log in to the admin with:
   - Username: `admin`
   - Password: `adminpass`  
   Then **change this password immediately** via the admin UI.

3. Add at least one OER source:

   - In admin, go to **Resources → OER sources → Add**.
   - Use the **Quick Configuration Presets** panel:
     - For richest metadata (best for types/identifiers/subjects), choose **📜 MARCXML / Dump Sources → OAPEN MARCXML**.
     - For OAI‑PMH, choose **📚 OAI-PMH Sources → OAPEN OAI-PMH** or **DOAB OAI-PMH**.
   - Save the new source.

4. Run a manual harvest:

   - From the main dashboard, trigger a harvest for your new source (or run the appropriate management command inside the `web` container, see below).
   - Once complete, confirm resources appear on the dashboard and in AI / Advanced search.

5. (Optional) Run embeddings and enrichment:

   - Ensure `ENABLE_LLM_ENRICHMENT=true` and a compatible model is available at `LOCAL_LLM_URL`.
   - From the dashboard or via management commands, run the embedding job to populate `content_embedding` (and any AI summaries/subjects you enable).

---

## Common management commands (inside Docker)

> Best practice: run Django management commands inside the `web` container so DB settings remain consistent.

From the project root:

```
# Open a shell in the web container
docker compose exec web bash

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create or update superuser
python manage.py createsuperuser

# Harvest a specific source (example; adapt to your commands)
python manage.py run_harvest --source-id 1

# Normalise legacy resource types into normalised_type
python manage.py normalise_resource_types

# (Planned) Enrich subjects
python manage.py enrich_subjects
```

If you also use an `app` container against the same database, repeat migrations there:

```
docker compose exec app python manage.py migrate
```

---

## Search and filters (for librarians)

- **AI Search** (`/`): single box + facet sidebar (source, language, resource type, subject, licence). Resource types are collapsed into a small, controlled set (`book`, `chapter`, `article`, `video`, `course`, `other`) via `normalised_type`.
- **Advanced Search** (`/advanced-search/`): fielded search (title/author/ISBN/OCLC, Boolean operators) plus the same facets, backed by the same `OERResource` metadata and search engine.

Both modes share:

- Language and type filters normalised at harvest time (MARCXML and OAI‑PMH harvesters try to derive `normalised_type` and ISO‑like language codes).
- Identifier filters (ISBN/ISSN/OCLC) useful for precise matching against reading lists or catalogue records.

---

## Contributing / project status

This repository is an active development branch used to explore enhanced harvesting, AI enrichment, and data visualisation for OER at MMU. Contributions, issues, and suggestions from other libraries and educational institutions are welcome.

- Open an issue for bugs, harvesting quirks (e.g. mis‑typed resources), or feature ideas.
- Pull requests should target the `main` branch and include a brief description and, where relevant, a note on how changes affect harvesters, search, or admin workflows.

---

## License

TBC

