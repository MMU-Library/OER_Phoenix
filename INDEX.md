# Open Educational Resourcer - Complete File Index

## Project Status
Last Updated: October 16, 2025

### Recent Updates
- Enhanced admin interface with OER source management
- Added automated resource harvesting capabilities
- Implemented field mapping configuration
- Added new homepage with feature overview
- Integrated AI-powered semantic search

## 📁 Complete Project Structure

```
oer_rebirth/
│
├── 📄 Configuration Files
│   ├── docker-compose.yml              # Docker services orchestration
│   ├── Dockerfile                      # Python application container definition
│   ├── docker-entrypoint.sh            # Container initialization script
│   ├── requirements.txt                # Python dependencies
│   ├── .env.example                    # Environment variables template
│   ├── .env                            # Environment configuration (created)
│   ├── .gitignore                      # Git ignore patterns
│   └── setup.sh                        # Quick setup script
│
├── 📚 Documentation Files
│   ├── README.md                       # Main project documentation
│   ├── QUICKSTART.md                   # Quick start guide
│   ├── PROJECT_STRUCTURE.md            # Detailed architecture documentation
│   ├── PROJECT_SUMMARY.md              # Executive summary
│   ├── DEPLOYMENT_CHECKLIST.md         # Deployment guide
│   └── INDEX.md                        # This file - complete index
│
├── 🔧 Utility Scripts
│   ├── verify_setup.py                 # Setup verification script
│   └── manage.py                       # Django management CLI
│
├── 🏗️ Django Project (oer_rebirth/)
│   ├── __init__.py                     # Package init + Celery import
│   ├── settings.py                     # Django configuration
│   ├── urls.py                         # Project URL routing
│   ├── celery.py                       # Celery task queue config
│   ├── wsgi.py                         # WSGI server entry point
│   └── asgi.py                         # ASGI server entry point
│
├── 📦 Resources App (resources/)
│   │
│   ├── 🎯 Core Application Files
│   │   ├── __init__.py
│   │   ├── models.py                   # OERResource model with pgvector
│   │   ├── views.py                    # View functions
│   │   ├── urls.py                     # URL routing
│   │   ├── admin.py                    # Admin customization
│   │   ├── forms.py                    # Form definitions
│   │   ├── apps.py                     # App configuration
│   │   ├── tasks.py                    # Celery async tasks
│   │   └── ai_utils.py            # Langchain AI retrieval
│   │
│   ├── 🔌 Services (resources/services/)
│   │   ├── __init__.py
│   │   ├── ai_utils.py            # SentenceTransformer embeddings
│   │   ├── oer_api.py                  # OER Commons + OpenStax API
│   │   └── talis.py                    # Talis Aspire integration
│   │
│   └── 🛠️ Management Commands (resources/management/)
│       ├── __init__.py
│       └── commands/
│           ├── __init__.py
│           ├── fetch_oer.py            # Fetch OER resources command
│           └── export_talis.py         # Export to Talis command
│
├── 🎨 Templates (templates/)
│   │
│   ├── base.html                       # Base template with Bootstrap
│   │
│   ├── resources/                      # App templates
│   │   ├── search.html                 # AI search interface
│   │   ├── taliscsv_upload.html        # CSV upload form
│   │   ├── compare.html                # Resource comparison
│   │   ├── talis_preview.html          # Export preview
│   │   ├── export.html                 # Export form
│   │   └── export_success.html         # Success message
│   │
│   └── admin/resources/                # Admin templates
│       ├── csv_upload.html             # Admin CSV upload
│       └── oerresource_changelist.html # Custom list view
│
├── 🎭 Static Files (static/)
│   └── .gitkeep                        # Placeholder for static assets
│
└── 🐳 Docker Init (docker-entrypoint-initdb.d/)
    └── init-vector.sql                 # PostgreSQL pgvector setup
```

## 📖 Documentation Guide

### For Getting Started
1. **QUICKSTART.md** - Start here for installation and first steps
2. **README.md** - Comprehensive overview and features
3. **verify_setup.py** - Run this to check your setup

### For Development
1. **PROJECT_STRUCTURE.md** - Understanding the architecture
2. **PROJECT_SUMMARY.md** - Technical overview
3. **models.py** - Data models and database schema
4. **views.py** - Application logic and endpoints

### For Deployment
1. **DEPLOYMENT_CHECKLIST.md** - Complete deployment guide
2. **.env.example** - Configuration reference
3. **docker-compose.yml** - Service configuration

## 🔑 Key Files Explained

### Configuration & Setup

#### `docker-compose.yml`
Defines 5 services:
- **web**: Django application (port 8000)
- **db**: PostgreSQL 14 with pgvector
- **redis**: Message broker for Celery
- **celery**: Background task worker
- **celery-beat**: Task scheduler

#### `Dockerfile`
- Base image: Python 3.11 slim
- Installs system dependencies (gcc, libpq-dev, netcat)
- Installs Python packages from requirements.txt
- Working directory: /app

#### `requirements.txt`
Key dependencies:
- Django 5.2.1
- sentence-transformers 3.0.0
- langchain + langchain-community
- pgvector, psycopg2-binary
- celery[redis], redis
- torch, transformers

#### `.env.example` / `.env`
Environment variables:
- Django settings (SECRET_KEY, DEBUG, ALLOWED_HOSTS)
- Database credentials
- Celery/Redis URLs
- Talis API credentials (optional)

### Django Core

#### `oer_prototype/settings.py`
- Database configuration (PostgreSQL + pgvector)
- Installed apps and middleware
- Static files configuration
- Celery beat schedule (daily OER fetch)
- Security settings (dev vs prod)

#### `oer_prototype/urls.py`
- Admin panel: `/admin/`
- App routes: includes `resources.urls`

#### `oer_prototype/celery.py`
- Celery app configuration
- Auto-discovers tasks from installed apps
- Redis broker configuration

### Application Core

#### `resources/models.py`
**OERResource Model**:
```python
- embedding: VectorField(384)  # AI embedding
- title: CharField
- publisher: CharField
- source: CharField
- description: TextField
- license: CharField
- url: URLField
- accessibility: BooleanField
```

#### `resources/views.py`
View functions:
- `ai_search()` - Semantic search with scores
- `csv_upload()` - Talis CSV import
- `batch_ai_search()` - Batch resource matching
- `export_resources()` - Talis export
- `compare_view()` - Resource comparison
- `talis_preview()` - Export preview

#### `resources/urls.py`
URL patterns:
- `/` → Redirects to AI search
- `/ai-search/` → Search interface
- `/batch-upload/` → CSV upload
- `/batch-ai-search/` → Batch results
- `/compare/` → Comparison view
- `/export/` → Export form
- `/talis-preview/` → Preview
- `/download-csv/` → CSV download

#### `resources/tasks.py`
Celery tasks:
- `fetch_oer_resources_task()` - Scheduled resource fetch
- `export_to_talis()` - Async Talis export

### AI/ML Components

#### `resources/ai_utils.py`
**OERRetriever Class**:
- Uses Langchain + HuggingFace embeddings
- ChromaDB vector store
- Recursive text splitting
- Similarity search with scores

#### `resources/services/ai_utils.py`
**Functions**:
- `get_embedding_model()` - Singleton SentenceTransformer
- `generate_embeddings()` - Batch embedding generation
- Model: all-MiniLM-L6-v2 (384 dimensions)

### API Integrations

#### `resources/services/oer_api.py`
**OER Sources**:
- OER Commons API
- OpenStax API
- Configurable field mapping
- Nested value extraction
- Automatic embedding generation

#### `resources/services/talis.py`
**TalisClient Class**:
- OAuth 2.0 authentication
- `authenticate()` - Get access token
- `create_reading_list()` - Create list + add resources
- JSON:API format

### Management Commands

#### `resources/management/commands/fetch_oer.py`
```bash
python manage.py fetch_oer
```
Fetches resources from all configured sources

#### `resources/management/commands/export_talis.py`
```bash
python manage.py export_talis --resource-ids 1 2 3 --title "List"
```
Export resources to Talis reading list

### Templates

#### `templates/base.html`
- Bootstrap 5.1.3 integration
- Navigation bar
- Flash messages
- Block structure for inheritance

#### `templates/resources/search.html`
- Search form with query input
- Results display with similarity scores
- Resource cards with metadata
- Batch search results section

#### `templates/resources/taliscsv_upload.html`
- File upload form
- CSV format requirements
- Template download link

### Docker Configuration

#### `docker-entrypoint.sh`
- Waits for database
- Creates superuser (admin/adminpass)
- Runs on container start

#### `docker-entrypoint-initdb.d/init-vector.sql`
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```
Initializes pgvector extension

## 🚀 Quick Reference Commands

### Setup
```bash
# Verify setup
python verify_setup.py

# Start services
docker-compose up --build

# Stop services
docker-compose down
```

### Data Management
```bash
# Fetch OER resources
docker-compose exec web python manage.py fetch_oer

# Generate embeddings
docker-compose exec web python manage.py shell
>>> from resources.services.ai_utils import generate_embeddings
>>> generate_embeddings()
```

### Database
```bash
# Access database
docker-compose exec db psql -U postgres -d oer_rebirth

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### Debugging
```bash
# View logs
docker-compose logs -f web
docker-compose logs -f celery

# Django shell
docker-compose exec web python manage.py shell

# Database shell
docker-compose exec web python manage.py dbshell
```

## 📊 File Statistics

- **Total Files**: 70+
- **Python Files**: 25
- **HTML Templates**: 10
- **Configuration Files**: 8
- **Documentation Files**: 6
- **Docker Files**: 3

## 🔗 File Dependencies

### High-Level Dependencies
```
manage.py
  └── oer_rebirth/
      ├── settings.py → .env
      ├── urls.py → resources.urls
      └── celery.py → resources.tasks

resources/
  ├── models.py (Base)
  ├── views.py → models, forms, tasks, ai_utils
  ├── urls.py → views
  ├── admin.py → models, forms
  ├── forms.py → models
  ├── tasks.py → services/
  └── ai_utils.py → models, services/ai_utils

services/
  ├── ai_utils.py → models
  ├── oer_api.py → ai_utils, models
  └── talis.py → models
```

## 📝 Notes

- All Python files use UTF-8 encoding
- Django version: 5.2.1
- Python version: 3.11
- PostgreSQL version: 14
- Redis version: 7

## 🎯 Next Steps

1. Review **QUICKSTART.md** for setup instructions
2. Run `python verify_setup.py` to check installation
3. Configure `.env` with your settings
4. Run `docker-compose up --build`
5. Access http://localhost:8000

---

**Last Updated**: January 2025
**Project Version**: 1.0.0

**Last Updated**: January 2025
**Project Version**: 1.0.0
