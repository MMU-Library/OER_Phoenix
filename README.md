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

```bash
docker-compose exec db psql -U postgres -d OER_Resourcer_Database
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

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions, please open an issue on GitHub.

For issues and questions, please open an issue on GitHub.
