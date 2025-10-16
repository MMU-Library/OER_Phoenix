# Open Educational Resourcer - Quick Start Guide

This guide will help you get the Open Educational Resourcer platform up and running in minutes.

## Prerequisites

Before you begin, ensure you have the following installed:
- **Docker Desktop** (for Windows/Mac) or **Docker Engine** (for Linux)
- **Docker Compose** v2.0 or higher
- **Git** (to clone the repository)
- At least **4GB of free RAM** (for AI model loading)
- At least **5GB of free disk space**

### Step-by-Step Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/oer_rebirth.git
cd oer_rebirth
```

Note: Replace `yourusername` with your actual GitHub username after creating the repository.

### 2. Create Environment Configuration

Copy the example environment file and customize it:

```bash
# On Linux/Mac
cp .env.example .env

# On Windows PowerShell
Copy-Item .env.example .env
```

Edit `.env` with your preferred text editor:

```bash
# Minimal configuration for local development
DJANGO_SECRET_KEY=your-secret-key-change-this-in-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

DB_NAME=OER_rebirth
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Optional: Only needed if using Talis export
# TALIS_TENANT=your-tenant
# TALIS_CLIENT_ID=your-client-id
# TALIS_CLIENT_SECRET=your-client-secret
```

### 3. Build and Start the Application

```bash
docker-compose up --build
```

This will:
- Build the Python application container
- Download and configure PostgreSQL with pgvector
- Set up Redis for Celery
- Start Celery workers
- Run database migrations
- Start the Django development server

**First startup may take 5-10 minutes** as it downloads Docker images and Python packages.

### 4. Access the Application

Once you see `Quit the server with CONTROL-C`, the application is ready:

- **Web Interface**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
  - Username: `admin`
  - Password: `adminpass` (created automatically)

## Initial Setup Tasks

### Load Sample OER Resources

To populate the database with resources from OER Commons and OpenStax:

```bash
docker-compose exec web python manage.py fetch_oer
```

This will fetch up to 50 resources from each source.

### Generate Embeddings for AI Search

After loading resources, generate embeddings for semantic search:

```bash
docker-compose exec web python manage.py shell
```

Then in the Python shell:

```python
from resources.services.ai_utils import generate_embeddings
generate_embeddings()
exit()
```

**Note**: First-time embedding generation will download the SentenceTransformer model (~90MB) and may take a few minutes depending on the number of resources.

## Using the Platform

### 1. AI-Powered Semantic Search

1. Navigate to http://localhost:8000/ai-search/
2. Enter a natural language query, e.g.:
   - "introduction to calculus"
   - "biology textbook for high school"
   - "programming for beginners"
3. View results ranked by semantic similarity

### 2. Bulk CSV Upload

To upload resources from a CSV file:

1. Go to http://localhost:8000/batch-upload/
2. Download the CSV template
3. Fill in your resources
4. Upload the file

The CSV format for Talis Reading Lists:
```csv
Date Added,Title,Type,Item Link,Local Control Number,ISBN10,ISBN13,ISSN,EISSN,DOI,Importance,Note for Student,Part of
2024-01-15,Python Programming,Book,https://example.com,12345,,,,,10.1234/example,Essential,Great intro book,Module 1
```

### 3. Admin Interface

Access advanced features through the admin panel:

1. Go to http://localhost:8000/admin
2. Login with admin/adminpass
3. Manage resources, upload CSVs, and configure settings

## Common Commands

### View Application Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f db
```

### Stop the Application

```bash
docker-compose down
```

### Stop and Remove All Data

```bash
docker-compose down -v
```

### Restart Services

```bash
docker-compose restart web
docker-compose restart celery
```

### Access Database

```bash
docker-compose exec db psql -U postgres -d OER_Resourcer_Database
```

Useful SQL commands:
```sql
-- Count resources
SELECT COUNT(*) FROM resources_oerresource;

-- View resources with embeddings
SELECT id, title, embedding IS NOT NULL as has_embedding 
FROM resources_oerresource LIMIT 10;

-- Exit
\q
```

### Create Django Superuser

If you need to create additional admin users:

```bash
docker-compose exec web python manage.py createsuperuser
```

### Run Database Migrations

If you modify models:

```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

## Troubleshooting

### Issue: Port 8000 Already in Use

**Solution**: Change the port in `docker-compose.yml`:

```yaml
services:
  web:
    ports:
      - "8080:8000"  # Change 8000 to 8080
```

Then access at http://localhost:8080

### Issue: Database Connection Failed

**Symptoms**: "could not connect to server" errors

**Solution**:
1. Check if PostgreSQL is healthy:
   ```bash
   docker-compose ps
   ```
2. Restart the database:
   ```bash
   docker-compose restart db
   ```
3. Check logs:
   ```bash
   docker-compose logs db
   ```

### Issue: AI Search Returns No Results

**Possible causes**:
1. No resources in database
   - **Solution**: Run `python manage.py fetch_oer`
2. Embeddings not generated
   - **Solution**: Run embedding generation script
3. Vector store not initialized
   - **Solution**: Restart the web service

### Issue: Slow First Search

**Cause**: Vector store initialization on first query

**Solution**: This is normal. Subsequent searches will be faster. For production, pre-initialize the vector store.

### Issue: Celery Tasks Not Running

**Check celery worker status**:
```bash
docker-compose logs celery
```

**Restart celery**:
```bash
docker-compose restart celery celery-beat
```

### Issue: Out of Memory

**Symptoms**: Container crashes, "Killed" messages

**Solution**: Increase Docker memory allocation:
- Docker Desktop → Settings → Resources → Memory
- Increase to at least 4GB

### Issue: Permission Denied on Linux

**Solution**: Add execute permission to scripts:
```bash
chmod +x docker-entrypoint.sh setup.sh
```

## Development Workflow

### Making Code Changes

1. Edit files in your local directory
2. Changes are automatically synced to the container (via volumes)
3. Django auto-reloads on file changes
4. For Celery changes, restart: `docker-compose restart celery`

### Running Tests

```bash
docker-compose exec web python manage.py test
```

### Accessing Python Shell

```bash
docker-compose exec web python manage.py shell
```

### Installing New Python Packages

1. Add package to `requirements.txt`
2. Rebuild the container:
   ```bash
   docker-compose up --build
   ```

## Production Deployment

For production deployment:

1. Update `.env`:
   ```bash
   DJANGO_DEBUG=False
   DJANGO_SECRET_KEY=<generate-strong-secret-key>
   DJANGO_ALLOWED_HOSTS=your-domain.com
   ```

2. Use production-grade database credentials

3. Configure HTTPS/SSL termination (nginx reverse proxy)

4. Set up proper backup strategy for PostgreSQL

5. Configure Celery with proper concurrency settings

6. Monitor with tools like Sentry, Prometheus, or New Relic

## Next Steps

- Explore the **Admin Panel** to manage resources
- Configure **Talis API credentials** for reading list export
- Customize **OER data sources** in `resources/services/oer_api.py`
- Add custom **CSS/JavaScript** in the `static/` directory
- Review **PROJECT_STRUCTURE.md** for detailed architecture

## Getting Help

- Check **README.md** for comprehensive documentation
- Review **PROJECT_STRUCTURE.md** for file organization
- Open an issue on GitHub
- Check Docker logs for error messages

## Useful Links

- Django Documentation: https://docs.djangoproject.com/
- pgvector Documentation: https://github.com/pgvector/pgvector
- SentenceTransformers: https://www.sbert.net/
- Celery Documentation: https://docs.celeryproject.org/

---

**Congratulations!** You now have a fully functional AI-powered OER platform. Happy searching! 🎉
