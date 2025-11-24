# Open Educational Resourcer - AI-Powered Educational Resource Platform

A Django-based platform supporting AI-powered semantic search, multi-source OER ingestion (OER Commons, OpenStax), vector search with pgvector, and Talis reading list export. Containerized with Docker and asynchronous tasks handled via Celery + Redis.

## Core Architecture

- **Backend**: Django 5.2.1
- **Database**: PostgreSQL 14 with pgvector extension (384-dimensional vector embeddings)
- **AI/ML**: HuggingFace Transformers, SentenceTransformers (model: all-MiniLM-L6-v2)
- **Vector Search**: pgvector with cosine similarity
- **Task Queue**: Celery + Redis
- **Containerization**: Docker Compose
- **Frontend**: Django templates + Bootstrap

## Features

- 🔍 **AI-Powered Semantic Search**: Use natural language to find relevant educational resources
- 📚 **Multi-Source OER Ingestion**: Automatically fetch resources from OER Commons and OpenStax
- 🎯 **Vector Similarity Search**: Find semantically similar resources using pgvector
- 📤 **Talis Reading List Export**: Export curated resources to Talis Aspire
- 📊 **CSV Bulk Upload**: Import resources from CSV files
- 🔄 **Async Task Processing**: Background processing with Celery

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd oer_rebirth
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Build and start the services:
```bash
docker-compose up --build
```

4. Access the application:
- Web interface: http://localhost:8000
- Admin panel: http://localhost:8000/admin (username: admin, password: adminpass)

## Usage

### Fetching OER Resources

Run the management command to fetch resources from external APIs:

```bash
docker-compose exec web python manage.py fetch_oer
```

### Generating Embeddings

After adding resources, generate embeddings for semantic search:

```bash
docker-compose exec web python manage.py shell
>>> from resources.services.ai_utils import generate_embeddings
>>> generate_embeddings()
```

### AI Search

Navigate to http://localhost:8000/ai-search/ and enter your query to find relevant resources using semantic search.

### CSV Upload

1. Go to http://localhost:8000/batch-upload/
2. Download the template CSV
3. Fill in your resources
4. Upload the CSV file

### Exporting to Talis

1. Configure Talis API credentials in `.env`
2. Use the export functionality in the web interface
3. Or use the management command:

```bash
docker-compose exec web python manage.py export_talis --resource-ids 1 2 3 --title "My Reading List"
```

## Project Structure

```
oer_rebirth/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── manage.py
├── oer_rebirth/
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── resources/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── forms.py
│   ├── tasks.py
│   ├── ai_processing.py
│   ├── services/
│   │   ├── ai_processing.py
│   │   ├── oer_api.py
│   │   └── talis.py
│   └── management/
│       └── commands/
│           ├── fetch_oer.py
│           └── export_talis.py
└── templates/
```

## Development

### Running Tests

```bash
docker-compose exec web python manage.py test
```

### Creating Migrations

```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

### Accessing the Database

The database runs inside Docker by default. There are two recommended ways
to access it:

- Using the bundled PGAdmin web UI (recommended for reproducible dev environments)
- Connecting from your host (VS Code / PGAdmin desktop) — requires the
  optional `docker-compose.override.yml` which maps the DB port to localhost.

Using PGAdmin (containerized)
OAPENLibrary_MARCXML_books.xml
1. Start services: `docker-compose up --build` (PGAdmin is included in the
   compose file and is accessible at `http://localhost:8080`).
2. Login to PGAdmin with the default credentials:
  - Email: `admin@example.com`
   - Password: `adminpass`
3. Add a new server in PGAdmin (right-click Servers → Create → Server):
   - **General / Name**: Postgres (docker)
   - **Connection**:
     - Hostname/address: `db`  # Docker service name
     - Port: `5432`
     - Maintenance DB: the value of `DB_NAME` in your `.env` (default: `oer_rebirth`)
     - Username: use `DB_USER` from `.env` (default: `postgres`)
     - Password: use `DB_PASSWORD` from `.env` (default: `postgres`)

Connecting from VS Code or host tools

- If you prefer to use desktop PGAdmin or VS Code's Postgres extensions, enable
  host access by creating `docker-compose.override.yml` (we provide one: it maps
  the DB port `5432` to your localhost). With the override in place, connect to:
  - Host: `localhost`
  - Port: `5432`
  - Username/password: as defined in `.env` (`DB_USER` / `DB_PASSWORD`).
- Note: exposing the DB port to your host may conflict with any locally-run
  Postgres instances. The project default keeps the DB internal to Docker and
  uses the PGAdmin container for inspection.

Using the provided `docker-compose.override.yml`

- Run the override (Docker Compose automatically picks up `docker-compose.override.yml`):

```bash
docker-compose up --build
```

- The override maps `5432:5432` so host tools can connect to `localhost:5432`.

Accessing psql inside the DB container

```bash
docker-compose exec db psql -U postgres -d oer_rebirth
```

## API Integrations

### OER Commons
- Endpoint: https://www.oercommons.org/api/resources
- Authentication: None required
- Rate Limits: Check their documentation

### OpenStax
- Endpoint: https://api.openstax.org/api/v2/resources
- Authentication: None required
- Rate Limits: Check their documentation

### Talis Aspire
- Authentication: OAuth 2.0 Client Credentials
- Required environment variables:
  - TALIS_TENANT
  - TALIS_CLIENT_ID
  - TALIS_CLIENT_SECRET

## Contributing

## MARCXML Dumps and Presets

- The project now supports importing MARCXML dumps (book-level metadata). We prefer using `pymarc` for robust MARC21 parsing; `pymarc` is included in `requirements.txt`.
- The OAPEN public MARCXML books dump (working link) is pre-configured as a preset: `https://memo.oapen.org/file/oapen/OAPENLibrary_MARCXML_books.xml`.
- To add a MARCXML source in the admin: set `Source Type` to `MARCXML`, paste the `MARCXML URL` (for example the OAPEN URL above), and click `Test` then `Harvest`.

Notes on `test` vs `harvest` for large dumps:
- The `Test` action performs a lightweight HEAD/GET to confirm the URL and content looks like MARCXML, but large dumps may not be fully interrogated by `Test`.
- Use `Harvest` to perform the full import; set `Max resources per harvest` to a small value (e.g., 50) for smoke tests.

If you expect more complex MARC sources, consider installing `MARCEdit` or adjusting mapping rules in `OERSourceFieldMapping`.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions, please open an issue on GitHub.

For issues and questions, please open an issue on GitHub.

## Demo / Troubleshooting (Quick Checklist)

- Create a Django superuser for Admin access:

```bash
python manage.py createsuperuser
```

- Run migrations and start the server:

```bash
python manage.py migrate
python manage.py runserver
```

- Quick AI search smoke test (Django shell):

```bash
python manage.py shell
>>> from resources.services.search_engine import OERSearchEngine
>>> engine = OERSearchEngine()
>>> print([ (r.resource.id, r.resource.title, r.final_score) for r in engine.hybrid_search('introduction to calculus', limit=5) ])
```

- If you plan to use Qdrant for scalable semantic search:
  - Ensure the Qdrant service is running (included in `docker-compose.yml`).
  - Populate `OERResource.content_embedding` for your resources (see `resources.services.ai_utils.generate_embeddings`).
  - Reindex into Qdrant:

```bash
python manage.py reindex_qdrant
```

- Notes & common fixes:
  - The semantic search prefers the `subject` model field (the UI accepts `subject_area` as a friendly name but it maps to `subject` internally).
  - If Qdrant search fails due to client API differences, ensure `qdrant-client` is installed in your environment. The code contains compatibility shims for multiple `qdrant-client` versions.
  - If you see no semantic hits, the system will fall back to a keyword-based search; ensure resources have `content_embedding` populated for best semantic results.

This README section contains the minimal steps to demo the AI search and the admin UI. For reproducible demos, run the compose stack and create a superuser before harvesting or importing resources.
