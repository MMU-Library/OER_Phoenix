# Open Educational Resourcer - Project Summary

## Overview

The Open Educational Resourcer is a comprehensive AI-powered educational resource platform that enables institutions to discover, manage, and export Open Educational Resources (OER). The platform leverages cutting-edge AI technologies for semantic search and integrates with major OER repositories and Talis Aspire reading lists. With an enhanced admin interface for OER source management and automated harvesting capabilities, the platform streamlines the process of collecting and organizing educational resources.

## Key Features

### 🔍 AI-Powered Semantic Search
- Natural language query processing
- Vector-based similarity search using pgvector
- 384-dimensional embeddings via SentenceTransformers
- Real-time relevance scoring
- Context-aware resource matching

### 📚 Multi-Source OER Integration
- **OER Commons** API integration
- **OpenStax** API integration
- Extensible architecture for additional sources
- Automated daily resource fetching
- Duplicate detection and prevention

### 🎯 Advanced Search Capabilities
- Semantic understanding of queries
- Batch resource matching
- Comparative resource analysis
- Accessibility-aware filtering
- License-based filtering

### 📤 Talis Aspire Integration
- OAuth 2.0 authentication
- Automated reading list creation
- Bulk resource export
- Asynchronous processing
- Status tracking

### 📊 Bulk Operations
- CSV import from Talis reading lists
- Batch resource upload
- Automated embedding generation
- Progress tracking
- Error handling and reporting

## Technical Architecture

### Backend Stack
```
Django 5.2.1
├── PostgreSQL 14 + pgvector
├── Redis (Message Broker)
├── Celery (Task Queue)
└── Python 3.12
```

### AI/ML Stack
```
Langchain Framework
├── SentenceTransformers (all-MiniLM-L6-v2)
├── HuggingFace Transformers
├── ChromaDB (Vector Store)
└── pgvector (Production Vector DB)
```

### Infrastructure
```
Docker Compose
├── Web (Django Application)
├── Database (PostgreSQL + pgvector)
├── Redis (Celery Broker)
├── Celery Worker
└── Celery Beat (Scheduler)
```

## Project Structure

```
oer_rebirth/
├── docker-compose.yml              # Service orchestration
├── Dockerfile                      # Application container
├── requirements.txt                # Python dependencies
├── manage.py                       # Django CLI
├── .env.example                    # Configuration template
│
├── oer_rebirth/                    # Django project
│   ├── settings.py                 # Configuration
│   ├── urls.py                     # URL routing
│   ├── celery.py                   # Celery setup
│   └── wsgi.py                     # WSGI entry point
│
├── resources/                      # Main application
│   ├── models.py                   # Data models
│   ├── views.py                    # View logic
│   ├── urls.py                     # App routes
│   ├── admin.py                    # Admin interface
│   ├── forms.py                    # Form definitions
│   ├── tasks.py                    # Celery tasks
│   ├── ai_processing.py            # Langchain integration
│   │
│   ├── services/                   # Business logic
│   │   ├── ai_processing.py        # Embedding generation
│   │   ├── oer_api.py              # API clients
│   │   └── talis.py                # Talis integration
│   │
│   └── management/commands/        # CLI commands
│       ├── fetch_oer.py            # Resource fetching
│       └── export_talis.py         # Export command
│
├── templates/                      # HTML templates
│   ├── base.html                   # Base template
│   └── resources/                  # App templates
│
├── static/                         # Static assets
│
└── docker-entrypoint-initdb.d/     # Database init
    └── init-vector.sql             # pgvector setup
```

## Core Components

### 1. OERResource Model
```python
class OERResource(models.Model):
    embedding = VectorField(dimensions=384)  # AI embedding
    title = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200)
    source = models.CharField(max_length=100)
    description = models.TextField()
    license = models.CharField(max_length=500)
    url = models.URLField()
    accessibility = models.BooleanField(default=True)
```

### 2. AI Processing Pipeline
```
User Query
    ↓
Text Embedding (SentenceTransformer)
    ↓
Vector Search (pgvector/ChromaDB)
    ↓
Similarity Scoring
    ↓
Ranked Results
```

### 3. Resource Ingestion Pipeline
```
External API (OER Commons/OpenStax)
    ↓
Data Mapping
    ↓
Duplicate Check
    ↓
Database Insert
    ↓
Embedding Generation
    ↓
Vector Index Update
```

### 4. Export Pipeline
```
Resource Selection
    ↓
Celery Task Queued
    ↓
Talis Authentication (OAuth 2.0)
    ↓
Reading List Creation
    ↓
Resource Addition
    ↓
Completion Notification
```

## API Integrations

### OER Commons
- **Endpoint**: `https://www.oercommons.org/api/resources`
- **Authentication**: None
- **Rate Limit**: TBD
- **Data Format**: JSON
- **Fields**: title, description, url, license

### OpenStax
- **Endpoint**: `https://api.openstax.org/api/v2/resources`
- **Authentication**: None
- **Rate Limit**: TBD
- **Data Format**: JSON:API
- **Fields**: attributes.{title, description, url, license}

### Talis Aspire
- **Endpoint**: `https://rl.talis.com/3/`
- **Authentication**: OAuth 2.0 Client Credentials
- **Rate Limit**: Based on subscription
- **Data Format**: JSON:API
- **Operations**: Create lists, add items

## Data Flow

### Search Flow
```
1. User enters query → POST /ai-search/
2. OERRetriever.build_vector_store()
3. Langchain similarity_search_with_score()
4. Score normalization (0-100%)
5. Results rendered in template
```

### Import Flow
```
1. CSV uploaded → POST /batch-upload/
2. CSV parsing and validation
3. OERResource.objects.create()
4. Session stores resource IDs
5. Redirect to /batch-ai-search/
6. Find similar resources for each
7. Display grouped results
```

### Scheduled Tasks
```
Celery Beat (Daily at midnight)
    ↓
fetch_oer_resources_task()
    ↓
Fetch from all configured sources
    ↓
Create/update resources
    ↓
generate_embeddings()
    ↓
Update vector index
```

## Performance Characteristics

### Search Performance
- **Embedding Generation**: ~50ms per query
- **Vector Search**: ~100-500ms (depends on dataset size)
- **Total Search Time**: ~200-600ms
- **Scalability**: Linear with dataset size

### Embedding Generation
- **Speed**: ~10-50 resources/second
- **Memory**: ~2GB for model + embeddings
- **Batch Size**: 50 (configurable)
- **First Time**: Downloads ~90MB model

### Database Performance
- **pgvector**: O(log n) for approximate search
- **Exact search**: O(n) but with HNSW index
- **Insert**: ~1ms per resource
- **Embedding update**: ~2ms per resource

## Security Features

### Application Security
- CSRF protection on all forms
- SQL injection prevention (Django ORM)
- XSS protection (template escaping)
- Secure password hashing (PBKDF2)
- Session management with secure cookies

### API Security
- OAuth 2.0 for Talis
- Environment-based secrets
- No hardcoded credentials
- Secure HTTP only in production

### Infrastructure Security
- Container isolation
- Database user permissions
- Network segmentation
- Health check endpoints

## Deployment Options

### Development (Current Setup)
```bash
docker-compose up
```
- SQLite or PostgreSQL
- DEBUG=True
- No SSL
- Local volumes

### Production (Recommended)
```bash
docker-compose -f docker-compose.prod.yml up -d
```
- PostgreSQL with pgvector
- DEBUG=False
- SSL/TLS required
- Named volumes
- Resource limits
- Health checks
- Log aggregation

### Cloud Deployment Options
- **AWS**: ECS + RDS + ElastiCache
- **Google Cloud**: Cloud Run + Cloud SQL + Memorystore
- **Azure**: Container Instances + PostgreSQL + Redis Cache
- **Heroku**: Heroku Postgres + Heroku Redis

## Scalability

### Horizontal Scaling
- Multiple web containers behind load balancer
- Multiple Celery workers
- Redis cluster for high availability
- Read replicas for database

### Vertical Scaling
- Increase container resources
- Optimize database queries
- Add indexes
- Cache frequently accessed data
- Use CDN for static files

## Monitoring and Observability

### Recommended Tools
- **APM**: Sentry, New Relic, Datadog
- **Logs**: ELK Stack, Loki, CloudWatch
- **Metrics**: Prometheus + Grafana
- **Uptime**: Pingdom, UptimeRobot
- **Database**: pgAdmin, DataGrip

### Key Metrics
- Response time (p50, p95, p99)
- Error rate
- Search accuracy
- Resource fetch success rate
- Celery task queue length
- Database query time
- Memory usage
- CPU usage

## Future Enhancements

### Planned Features
- [ ] Multi-language support
- [ ] Advanced filtering (subject, level, format)
- [ ] User accounts and saved searches
- [ ] Resource ratings and reviews
- [ ] RESTful API for external integration
- [ ] GraphQL API option
- [ ] Resource usage analytics
- [ ] Automated quality assessment
- [ ] Batch export to multiple formats
- [ ] Integration with LMS platforms

### Technical Improvements
- [ ] Elasticsearch for full-text search
- [ ] Redis caching layer
- [ ] CDN integration
- [ ] Database query optimization
- [ ] Automated testing suite
- [ ] CI/CD pipeline
- [ ] Kubernetes deployment
- [ ] Service mesh implementation

## Cost Considerations

### Infrastructure Costs (Monthly)
- **Small**: $50-100 (1-100 users)
  - 1 CPU, 2GB RAM
  - 20GB storage
  - Basic RDS instance
  
- **Medium**: $200-500 (100-1000 users)
  - 2 CPU, 4GB RAM
  - 100GB storage
  - Multi-AZ RDS
  - Redis cache
  
- **Large**: $1000+ (1000+ users)
  - Auto-scaling groups
  - Load balancer
  - High-availability setup
  - CDN

### AI/ML Costs
- **SentenceTransformer**: Free (open-source)
- **Embedding Storage**: ~1KB per resource
- **Compute**: CPU-based (no GPU required)
- **API Calls**: Depends on usage of external APIs

## Support and Maintenance

### Regular Maintenance
- Weekly dependency updates
- Monthly security patches
- Quarterly feature releases
- Daily automated backups
- 24/7 monitoring

### Support Channels
- GitHub Issues for bugs
- Documentation wiki
- Email support
- Community forum (optional)

## License

[Specify your license here]

## Credits

### Technologies Used
- Django Framework
- PostgreSQL + pgvector
- SentenceTransformers
- Langchain
- Celery
- Bootstrap

### Data Sources
- OER Commons
- OpenStax
- Talis Aspire (integration)

## Contact

- **Project Lead**: [Name]
- **Email**: [Email]
- **Repository**: [GitHub URL]
- **Documentation**: [Docs URL]

---

**Last Updated**: January 2025
**Version**: 1.0.0
**Version**: 1.0.0
