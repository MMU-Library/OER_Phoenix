# Open Educational Resourcer - Complete Project Structure

This document provides a comprehensive overview of the project structure and all files.

## Project Root Files

```
.
├── docker-compose.yml          # Docker services orchestration
├── Dockerfile                  # Python application container
├── docker-docker-entrypoint.sh        # Container initialization script
├── requirements.txt            # Python dependencies
├── manage.py                   # Django management script
├── setup.sh                    # Quick setup script
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore patterns
└── README.md                   # Project documentation
```

## Django Project Structure

### oer_rebirth/ (Main Django Project)
```
oer_rebirth/
├── __init__.py                 # Package initialization with Celery
├── settings.py                 # Django settings and configuration
├── urls.py                     # Project URL configuration
├── celery.py                   # Celery configuration
├── wsgi.py                     # WSGI application entry point
└── asgi.py                     # ASGI application entry point
```

### resources/ (Main Django App)
```
resources/
├── __init__.py
├── models.py                   # OERResource model with pgvector
├── views.py                    # View functions for web interface
├── urls.py                     # App URL patterns
├── admin.py                    # Django admin customization
├── forms.py                    # Form definitions
├── apps.py                     # App configuration
├── tasks.py                    # Celery tasks
├── ai_utils.py            # Langchain-based AI retrieval
│
├── services/                   # Business logic services
│   ├── __init__.py
│   ├── ai_utils.py        # Sentence transformer embeddings
│   ├── oer_api.py              # External API integrations
│   └── talis.py                # Talis API client
│
└── management/                 # Django management commands
    ├── __init__.py
    └── commands/
        ├── __init__.py
        ├── fetch_oer.py        # Fetch OER resources command
        └── export_talis.py     # Export to Talis command
```

## Templates Structure

```
templates/
├── base.html                           # Base template with Bootstrap
├── resources/
│   ├── search.html                     # AI search interface
│   ├── taliscsv_upload.html           # CSV upload form
│   ├── compare.html                    # Resource comparison view
│   ├── talis_preview.html             # Talis export preview
│   ├── export.html                     # Export form
│   └── export_success.html            # Export success message
└── admin/
    └── resources/
        ├── csv_upload.html             # Admin CSV upload
        └── oerresource_changelist.html # Admin list view override
```

## Static Files

```
static/
└── .gitkeep                    # Placeholder for static assets
```

## Docker Configuration

```
docker-entrypoint-initdb.d/
└── init-vector.sql             # PostgreSQL pgvector extension initialization
```

## Key Features by File

### Core Models (resources/models.py)
- **OERResource**: Main model with pgvector embedding support
  - 384-dimensional vector field for semantic search
  - Title, description, source, license, URL fields
  - Publisher and accessibility metadata

### AI Processing (resources/services/ai_utils.py)
- **get_embedding_model()**: Singleton SentenceTransformer model
- **generate_embeddings()**: Batch embedding generation with pgvector

### Langchain Integration (resources/ai_utils.py)
- **OERRetriever**: Langchain-based vector store retrieval
- ChromaDB integration for similarity search
- Recursive text splitting for long documents

### API Integrations (resources/services/oer_api.py)
- OER Commons API integration
- OpenStax API integration
- Flexible field mapping for different API structures

### Talis Integration (resources/services/talis.py)
- **TalisClient**: OAuth 2.0 authentication
- Reading list creation
- Bulk resource addition

### Views (resources/views.py)
- **ai_search**: Semantic search with similarity scores
- **csv_upload**: Talis CSV import with validation
- **batch_ai_search**: Batch resource matching
- **export_to_talis**: Async export trigger

### Celery Tasks (resources/tasks.py)
- **fetch_oer_resources_task**: Scheduled OER fetching
- **export_to_talis**: Async Talis export

## Data Flow

### Search Flow
1. User submits query → `ai_search` view
2. `OERRetriever` builds vector store from database
3. Langchain performs similarity search
4. Results normalized and returned with similarity scores

### Import Flow
1. CSV uploaded → `csv_upload` view
2. Rows validated and parsed
3. `OERResource` instances created
4. Session stores IDs for batch processing
5. `batch_ai_search` finds similar resources

### Export Flow
1. Resources selected → `export_resources` view
2. Celery task `export_to_talis` queued
3. `TalisClient` authenticates via OAuth
4. Reading list created in Talis
5. Resources added to list

## Environment Variables

Required in `.env`:
- `DJANGO_SECRET_KEY`: Django secret key
- `DJANGO_DEBUG`: Debug mode (True/False)
- `DJANGO_ALLOWED_HOSTS`: Comma-separated hosts
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: PostgreSQL config
- `TALIS_TENANT`, `TALIS_CLIENT_ID`, `TALIS_CLIENT_SECRET`: Talis API credentials

## Docker Services

1. **web**: Django application server
2. **db**: PostgreSQL 14 with pgvector
3. **redis**: Message broker for Celery
4. **celery**: Background task worker
5. **celery-beat**: Scheduled task scheduler

## API Endpoints

### Web Interface
- `/`: Redirects to AI search
- `/ai-search/`: Semantic search interface
- `/batch-upload/`: CSV upload for batch processing
- `/compare/`: Side-by-side resource comparison
- `/talis-preview/`: Export preview
- `/export-to-talis/`: Talis export trigger
- `/admin/`: Django admin panel

## Management Commands

```bash
# Fetch OER resources from external APIs
python manage.py fetch_oer

# Export resources to Talis
python manage.py export_talis --resource-ids 1 2 3 --title "My List"
```

## Testing Strategy

1. **Unit Tests**: Model methods, form validation
2. **Integration Tests**: API integrations, Celery tasks
3. **E2E Tests**: Search flow, export flow

## Performance Considerations

- **Vector Search**: pgvector extension for fast similarity search
- **Batch Processing**: Celery for async tasks
- **Caching**: Redis for session and task state
- **Embedding Generation**: Batched processing with progress bars

## Security Features

- CSRF protection on all forms
- Environment-based DEBUG setting
- Secure cookie settings for production
- OAuth 2.0 for Talis API
- Database connection with health checks

## Deployment Checklist

1. ✓ Update `.env` with production values
2. ✓ Set `DJANGO_DEBUG=False`
3. ✓ Configure `DJANGO_ALLOWED_HOSTS`
4. ✓ Set strong `DJANGO_SECRET_KEY`
5. ✓ Configure Talis API credentials
6. ✓ Run migrations: `python manage.py migrate`
7. ✓ Create superuser: `python manage.py createsuperuser`
8. ✓ Collect static files: `python manage.py collectstatic`
9. ✓ Start services: `docker-compose up -d`

## Troubleshooting

### Database Connection Issues
- Check `docker-compose logs db`
- Verify `.env` database credentials
- Ensure pgvector extension is installed

### Embedding Generation Slow
- Check available system memory
- Reduce batch size in `generate_embeddings()`
- Use GPU if available (update requirements.txt)

### Celery Tasks Not Running
- Check `docker-compose logs celery`
- Verify Redis is running
- Check task registration in `celery.py`

### Search Returns No Results
- Ensure embeddings are generated
- Check vector store initialization
- Verify database contains resources

## Development Workflow

1. Make code changes
2. Run tests: `docker-compose exec web python manage.py test`
3. Check migrations: `docker-compose exec web python manage.py makemigrations --dry-run`
4. Apply migrations: `docker-compose exec web python manage.py migrate`
5. Restart services: `docker-compose restart web`

## Contributing Guidelines

1. Follow PEP 8 style guide
2. Add docstrings to new functions
3. Update this documentation for structural changes
4. Write tests for new features
5. Use meaningful commit messages

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: See README.md
- Contact: [your-email]
- Contact: [your-email]
