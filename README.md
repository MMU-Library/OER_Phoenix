
# Open Educational Resourcer

**AI-Powered Semantic Search Platform for OER**

A Django-based platform supporting advanced AI search, multi-source OER harvesting, vector search via pgvector/Qdrant, and Talis reading list export. Containerized for quick deployment with Docker, with async pipelines via Celery + Redis.

---

## 🚀 Core Architecture

- **Backend:** Django 5.x
- **Database:** PostgreSQL 14+ (with pgvector)
- **AI/ML:** HuggingFace/SentenceTransformers (`all-MiniLM-L6-v2`)
- **Vector Search:** pgvector (default), Qdrant optional
- **Task Queue:** Celery + Redis (async processing)
- **Containerization:** Docker Compose
- **Frontend:** Django templates + Bootstrap

---

## ✨ Features

- 🔍 **AI-Powered Semantic Search**: Find resources with natural language queries
- 📚 **OER Harvesting**: Automated ingestion from OER Commons, OpenStax, MARCXML, or CSV
- 🎯 **Vector Similarity Search**: Semantic relevance via pgvector/Qdrant
- 📤 **Talis Reading List Export**: Send collections to Talis Aspire
- 📊 **Admin Dashboard**: Manage sources, mappings, and ingest jobs
- 🔄 **Async Task Processing**: Embeddings/indexing offloaded to Celery
- 🗃 **Batch Upload**: Import resources in bulk from CSV
- 📝 **Extensible API**: Designed for easy integration

---

## 🟢 Quick Start

### Prerequisites

- [Docker](https://www.docker.com/get-started) & [Docker Compose](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/)

### Installation

Clone and start:
```
git clone https://github.com/MMU-Library/oer_rebirth.git
cd oer_rebirth
cp .env.example .env      # Edit secrets and config values as needed
docker compose up --build
```

**Access:**
- Web interface: http://localhost:8000
- Admin panel: http://localhost:8000/admin

---

### First Run Setup

1. **Create admin user:**
   ```
   docker compose exec web python manage.py createsuperuser
   ```
2. **Run migrations:**
   ```
   docker compose exec web python manage.py migrate
   ```

---

## 🔎 Semantic Search & Ingestion

- **Manual Resource Harvest/Import:**
   ```
   docker compose exec web python manage.py fetch_oer
   ```
- **Bulk Embedding (AI Search):**
   ```
   docker compose exec web python manage.py shell
   >>> from resources.services.ai_utils import generate_embeddings
   >>> generate_embeddings()
   ```
- **Try AI-powered search on http://localhost:8000 or:**
   ```
   docker compose exec web python manage.py shell
   >>> from resources.services.search_engine import OERSearchEngine
   >>> engine = OERSearchEngine()
   >>> engine.hybrid_search('example query', limit=3)
   ```

---

## 📚 CSV Upload

1. Visit http://localhost:8000/batch-upload/
2. Download CSV template, populate, and upload.

---

## 📤 Export to Talis

- Set Talis API credentials in `.env`.
- Use export from web portal or management command:
   ```
   docker compose exec web python manage.py export_talis --resource-ids 1 2 3 --title "Reading List"
   ```

---

## 🗂 Project Structure

```
oer_rebirth/
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── manage.py
├── oer_rebirth/
│   ├── settings.py
│   ├── celery.py
│   └── ...
├── resources/
│   ├── models.py
│   ├── views.py
│   ├── tasks.py
│   ├── services/
│   │   ├── ai_utils.py
│   │   ├── search_engine.py
│   │   ├── talis.py
│   └── management/
│       └── commands/
│           ├── fetch_oer.py
│           └── export_talis.py
├── templates/
└── ...
```

---

## Development

### Run Tests

```
docker compose exec web python manage.py test
```

### Create and Apply Migrations

```
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

### Access Database

- **psql inside container:**
  ```
  docker compose exec db psql -U postgres -d oer_rebirth
  ```
- **Optional:** expose port 5432 in `docker-compose.override.yml` for desktop tools/VS Code/PGAdmin.

---

## API Integrations

- **OER Commons:** https://www.oercommons.org/api/resources
- **OpenStax:** https://api.openstax.org/api/v2/resources
- **Talis Aspire:** OAuth 2.0 credentials via `.env` (see included notes)
- **MARCXML:** Supported via admin/preset with OAPEN and others

---

## Contributing

1. Fork the repo
2. Branch and commit changes
3. Open a Pull Request

---

## License

[Add your license info here]

---

## Support

- Open an issue on GitHub for troubleshooting or feature requests.
- For advanced integration, ask about Qdrant vector DB, MARCXML, or custom AI models.

---

## 📝 Troubleshooting & Common Tasks

- **Rebuild everything:**  
  ```
  docker compose down -v
  docker compose up --build
  ```
- **Re-generate and index embeddings for search:**  
  ```
  docker compose exec web python manage.py shell
  >>> from resources.services.ai_utils import generate_embeddings
  >>> generate_embeddings()
  ```

---

## Credits

Platform developed by Manchester Metropolitan University Library and Digital Services.

---

```

*You can adapt the language, credits, or API references according to internal/partner needs, but this README is fully plug-and-play for both local and cloud deployment and matches modern open-source standards for AI/semantic/OER toolkits.*

