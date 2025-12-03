
---

# OER_Rebirth  
Open Educational Resources Discovery & Analysis Platform for Academic Libraries  

A Django-based digital library system designed for UK academic subject librarians to discover OER and analyse Talis Aspire reading lists for open alternatives. Built for Manchester Metropolitan University Library Services.

---

## Overview  
OER_Rebirth aggregates open educational resources from multiple providers (OAPEN, DOAB, OER Commons, OpenStax) and provides:  
- **AI-powered semantic search** using sentence-transformers (all-MiniLM-L6-v2) with pgvector  
- **Talis Aspire reading list analysis**: upload CSV or link to a Talis list to find OER alternatives for each item  
- **Dashboard interface** for librarians with resource statistics, subject breakdowns, and maintenance tools  
- **Multi-source harvesting** via OAI-PMH, REST APIs, CSV, and MARCXML  
- **Self-hosted and open source**: Docker-based deployment, no vendor lock-in  

---

## Key Features  

### For Subject Librarians
- Dashboard landing page with AI search, Talis analysis widget, and resource statistics  
- Reading list coverage analysis: upload a Talis CSV export or paste a list URL to identify open alternatives for proprietary items  
- Semantic search: find OER by topic, learning outcome, or natural language query  
- Collection building: save analysis results and export back to Talis  

### For Administrators
- Unified source management: configure API, OAI-PMH, CSV, and MARCXML harvesters via admin interface  
- Automated harvesting: scheduled background jobs with status tracking and error logging  
- Embedding generation: batch or selective AI embedding creation for semantic search  
- Quality scoring: built-in metrics for resource assessment  

---

## Architecture  

### Technology Stack
- **Backend**: Django 5.x, Python 3.12  
- **Database**: PostgreSQL 16 with pgvector extension  
- **Search**: SentenceTransformers (all-MiniLM-L6-v2), cosine similarity  
- **Containerization**: Docker Compose  
- **Frontend**: Bootstrap 5, Chart.js  
- **APIs**: OAI-PMH, REST, Talis Aspire integration  

### Core Components  
```
oer_rebirth/
├── resources/ # Main Django app
│   ├── models.py # OERResource, OERSource, HarvestJob
│   ├── views.py # Dashboard, search, Talis analysis
│   ├── admin.py # Admin interface with harvesting tools
│   ├── services/
│   │   ├── ai_utils.py # Embedding generation (SentenceTransformers)
│   │   ├── search_engine.py # Semantic + keyword hybrid search
│   │   └── talis_analysis.py # Reading list OER matching
│   └── harvesters/ # API, OAI-PMH, CSV, MARCXML ingest
├── templates/
└── docker-compose.yml # PostgreSQL + Django services
```

---

## Installation  

### Prerequisites  
- Docker and Docker Compose  
- Git  

### Quick Start  
1. **Clone the repository**  
```bash
git clone https://github.com/MMU-Library/oer_rebirth.git
cd oer_rebirth
```  

2. **Configure environment variables**  
```bash
cp .env.example .env
```  
Key variables:  
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: Database credentials  
- `DJANGO_SECRET_KEY`: Generate via `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`  
- `EMBEDDING_MODEL_NAME`: Default `all-MiniLM-L6-v2`  
- `VECTOR_BACKEND`: Default `pgvector`  
- Optional: `TALIS_TENANT`, `TALIS_CLIENT_ID`, `TALIS_CLIENT_SECRET` for Talis API export  

3. **Build and start services**  
```bash
docker-compose build
docker-compose up
```  

4. **Run migrations and create superuser**  
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```  

5. **Access the platform**  
- Dashboard: http://localhost:8000/  
- Admin: http://localhost:8000/admin/  

---

## Usage  

### Initial Setup  
1. **Add OER sources** via admin at `/admin/resources/oersource/add/`  
   - Select source type (API, OAI-PMH, CSV, MARCXML)  
   - Configure endpoint and credentials  
   - Test connection before enabling  

2. **Run harvesters** to populate the OER corpus  
   - Use admin list actions or "Harvest" buttons on source detail pages  
   - Monitor progress via "Harvest jobs" in admin  

3. **Generate embeddings** for semantic search  
   - Admin: select resources → Actions → "Generate embeddings for selected resources"  
   - Dashboard (staff only): click "Generate missing embeddings" in maintenance card  

---

## API Endpoints  

### Search API  
**Endpoint:** `/api/search/`  
**Method:** GET  
**Parameters:**  
- `q` (required): search query  
- `limit` (optional): max results, default 10  

**Response:**  
```json
{
    "results": [
        {
            "id": 123,
            "title": "Introduction to Statistics",
            "url": "https://...",
            "score": 0.87,
            "source": "OpenStax",
            "resource_type": "Textbook"
        }
    ]
}
```

---

## Deployment  

### Production Considerations  
1. Use a production-grade WSGI server: Replace Django dev server with Gunicorn or uWSGI  
2. Serve static files via nginx or CDN: Configure `STATIC_ROOT` and run `collectstatic`  
3. Enable HTTPS: Use Let's Encrypt or institutional certificates  
4. Set `DEBUG=False` in production environment  
5. Configure `ALLOWED_HOSTS` with your domain  
6. Schedule background tasks: Use Celery or cron for harvesting and embedding generation  
7. Monitor logs: Centralize logs with ELK stack or similar  
8. Backup database: Regular PostgreSQL dumps  

---

## Contributing  

This project is developed for MMU Library Services but contributions are welcome.  

### Areas for Contribution  
- Additional OER provider integrations  
- Improved Talis Aspire API support  
- Quality scoring algorithms  
- Accessibility enhancements  
- Multi-language support  
- Performance optimizations  

### Development Workflow  
1. Fork the repository  
2. Create a feature branch (`git checkout -b feature/new-harvester`)  
3. Commit changes with clear messages  
4. Push to your fork and submit a pull request  

---

## License  
[Specify license: MIT, GPL, Apache 2.0, etc.]  

---

## Acknowledgements  
- Built on [sentence-transformers](https://www.sbert.net/) for semantic search  

---

## Contact  

**Project Lead:** [Your Name]  
**Institution:** Manchester Metropolitan University Library Services  
**Repository:** https://github.com/MMU-Library/oer_rebirth  

For questions or collaboration inquiries, open an issue on GitHub or contact the development team.

---
