
## Updated `README.md`

```markdown
# OER_Phoenix

OER_Phoenix is an open‑source discovery and analysis platform for Open Educational Resources (OER), developed at Manchester Metropolitan University Library Services.[web:1]

It aggregates OER from multiple providers (e.g. OAPEN, DOAB, OER Commons, OpenStax, MARCXML feeds), provides AI‑powered search for staff and students, and supports Talis Aspire reading‑list analysis and export.[web:1][file:88]

---

## Features

### Discovery & Search

- **AI Search**
  - Hybrid semantic + keyword ranking via `OERSearchEngine.hybrid_search` (pgvector + BM25).[file:3][file:88]
  - Faceted filters (source, language, resource type, subject) and sort options (relevance, newest, quality, title).[file:88]
  - Result cards with:
    - Source and match‑reason badges.
    - **AI confidence** badge (semantic similarity 0–1 shown as a percentage).
    - **Quality** badge (internal 0–5 quality score shown as a percentage).

- **Advanced Search**
  - Three‑row Boolean builder with fields:
    - Any field, Title, Author / Creator, Subject / Keywords, ISBN, ISSN, OCLC number.[file:88]
  - Additional limits for resource type and language.
  - Uses the same hybrid engine and result model as AI Search; results can be shown on the main results page or inline beneath the form.[file:88]

- **Dark mode**
  - Optional light/dark toggle at the layout level using CSS variables and Bootstrap classes in `base.html`.[file:39]

### Talis Aspire Workflows

- Upload a Talis CSV or fetch a list by URL from the dashboard widget.[file:88]
- Parse into a normalised `TalisList` in session (`talis.py`).[file:88]
- Run AI matching per list item via the hybrid search engine and generate:
  - Coverage summary (% of items with OER matches).
  - Breakdown by resource type and other facets.[file:88]
- Export reports as CSV and optionally push to Talis via `TalisPushJob` and Celery tasks.[file:88]

### Data, Identifiers & Harvesting

- **Models**
  - `OERSource` – configuration for each provider (API, OAI‑PMH, CSV, MARCXML) with status and schedule.[file:39]
  - `OERResource` – core resource model:
    - Descriptive: title, description, subject, level, publisher, author, resource_type, format, license, language.[file:39]
    - Identifiers: `isbn`, `issn`, `oclc_number`, `doi` for precise matching and export.[file:39]
    - AI: `content_embedding`, `keywords`, `ai_generated_summary`, `title_en`, `description_en`.[file:39]
    - Quality: `overall_quality_score` (0–5, exposed as a percentage in the UI).[file:88]
  - `HarvestJob` and `TalisPushJob` – track harvesting runs and outbound report pushes.[file:39]

- **Harvesters**
  - Generic harvesters for API, OAI‑PMH, and CSV in `resources/harvesters/`.[web:1]
  - `MARCXMLHarvester`:
    - Uses `pymarc.parse_xml_to_array` when available, falling back to ElementTree for robustness.[file:90]
    - Extracts title, authors, publisher, language, description, ISBN, and 856$u URLs.
    - **URL hardening:** only strings starting with `http://` or `https://` are stored in `OERResource.url`; ONIX‑style filenames and bare ISBNs are no longer used as external links.[file:90]

### Frontend & Templates

- Bootstrap 5‑based UI with a fixed top navbar, dark‑mode toggle, and responsive grid layouts.[file:39]
- Dashboard charts (resource‑type breakdown, etc.) using Chart.js.[file:39]
- Template tags in `resources/templatetags/oer_filters.py`:
  - `language_badge`, `source_badge`, `match_reason_badge`, `star_rating`, `multiply`.[file:90]
  - `link_type_button(resource)`:
    - Detects PDFs, EPUBs, video, DOI links, repositories, and generic web pages to label buttons appropriately.
    - Only treats values that already look like real URLs as external links; non‑URL strings (e.g. ONIX filenames) fall back to a safe “View record” link instead of a broken external URL.[file:90]

---

## Architecture

- **Backend:** Django 5, Python 3.12.[web:1]
- **Database:** PostgreSQL with `pgvector` extension via `pgvector.django`.[file:39]
- **Search engine:** `resources/services/search_engine.py`
  - Embedding generation (SentenceTransformers model, configurable via settings).
  - Cosine similarity over `content_embedding` combined with keyword scores.
  - Faceting and filter application (source, language, resource_type, subject, etc.).[file:3]
- **Async / background:** Celery + Redis for harvest jobs, embedding generation, and Talis push tasks.[web:1]
- **Containers:** `docker-compose.yml` orchestrates:
  - `web` (Django app), `db` (pgvector/Postgres), `redis`, `celery`, `celery-beat`,
  - `pgadmin` for DB inspection, and `qdrant` (reserved for future vector search experiments).[web:1]

---

## Repository Layout (selected)

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
│   ├── templatetags/
│   │   └── oer_filters.py       # Badges, scores, link‑type logic
│   └── templates/resources/
│       ├── dashboard.html
│       ├── search.html
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
cp .env.example .env   # if present; otherwise create .env
```

Set at least in `.env`:[web:1]

- `DJANGO_SECRET_KEY` – a strong random key.
- `POSTGRES_DB=oer_rebirth`
- `POSTGRES_USER=postgres`
- `POSTGRES_PASSWORD=postgres`

Optional but recommended:

- `LOCAL_LLM_URL`, `LOCAL_LLM_MODEL`, `LOCAL_LLM_TIMEOUT` – for local enrichment (see `settings.py`).[file:69]
- `ENABLE_LLM_ENRICHMENT` – enable/disable AI enrichment.
- Talis integration settings (`TALIS_API_URL`, etc.) if using push‑back.

### 2. Build and start containers

```
docker compose build
docker compose up -d
```

The `web` container’s `docker-entrypoint.sh` will:[web:1]

- Wait for Postgres (`pg_isready`).
- Ensure the database exists and enable the `vector` extension.
- Run `makemigrations` and `migrate`.
- Create a default superuser (`admin` / `adminpass`) if one does not already exist.

### 3. Access the application

- Dashboard & AI Search: <http://localhost:8000/>  
- Advanced Search: <http://localhost:8000/advanced-search/>  
- Admin: <http://localhost:8000/admin/>

---

## Development Workflow

> Best practice: run Django management commands inside the `web` container so DB settings remain consistent.

Common commands:

```
# Shell into the web container
docker compose exec web bash

# Inside the container:
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py shell
```

For iterative frontend work, edit templates and static files on the host; Django’s auto‑reload inside the container will pick up changes.

---

## Roadmap & Contributions

Potential next steps:

- Extend `search_engine._apply_filters` to fully exploit `isbn`, `issn`, and `oclc_number` filters from Advanced Search.[file:3][file:88]
- Additional source presets and mapping helpers (e.g. per‑provider URL normalisation).
- Richer per‑result diagnostics in Advanced Search (e.g. explicit “matched on ISBN/OCLC” messaging).
- Expanded documentation for Talis workflows and best practices for OER remediation.


---

## License & Credits

- License: _TBC_ (add once selected).  
- Uses libraries including Django, Celery, pgvector, `sentence-transformers`, `pymarc`, Bootstrap 5, and Chart.js.[web:1][file:3]  
- Developed by Manchester Metropolitan University Library Services.

```