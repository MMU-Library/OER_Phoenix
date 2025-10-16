# Pre-Launch Checklist for Trial Run

## ✅ Current Status
All files verified and in place!

## Quick Trial Run Steps

### 1. Environment Check (DONE ✅)
- [x] All files present
- [x] .env file configured
- [x] Docker Compose file valid

### 2. Launch Services

```bash
# Start all services
docker-compose up --build
```

**Expected output:**
- ✅ PostgreSQL starts and becomes healthy
- ✅ Redis starts
- ✅ Web service starts on port 8000
- ✅ Celery worker starts
- ✅ Celery beat starts

**Wait for:** `Quit the server with CONTROL-C.`

### 3. Access Points to Test

Once services are running:

#### A. Web Interface
- **URL**: http://localhost:8000
- **Expected**: Redirect to AI search page

#### B. Admin Panel
- **URL**: http://localhost:8000/admin
- **Credentials**: 
  - Username: `admin`
  - Password: `adminpass`
- **Expected**: Enhanced Django admin interface with:
  - OER Source management with harvest functionality
  - Harvest job monitoring
  - Field mapping configuration
  - Status badges and action buttons

#### C. Home Page
- **URL**: http://localhost:8000
- **Expected**: Landing page with:
  - Feature cards for main functionality
  - Quick access to AI search, batch upload, and comparison tools
  - Admin tools section
  - Getting started guide

#### D. API Search
- **URL**: http://localhost:8000/ai-search/
- **Expected**: Search form loads

### 4. Database Check

In a new terminal:

```bash
# Check database connection



# Check pgvector extension
docker-compose exec db psql -U postgres -d oer_rebirth_Database -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Check if tables exist (after migration)
docker-compose exec db psql -U postgres -d oer_rebirth -c "\dt"
```

### 5. Run Migrations

```bash
# Django migrations (should run automatically, but can run manually)
docker-compose exec web python manage.py migrate

# Create superuser (if not auto-created)
docker-compose exec web python manage.py createsuperuser
```

### 6. Test Basic Functionality

#### A. Admin Access
1. Go to http://localhost:8000/admin
2. Login with admin/adminpass
3. Navigate to OER Resources
4. Should see empty list or any existing resources

#### B. Search Page
1. Go to http://localhost:8000/ai-search/
2. Search form should be visible
3. Try searching (will return no results if no data loaded)

### 7. Load Sample Data (Optional)

```bash
# Fetch OER resources from external APIs
docker-compose exec web python manage.py fetch_oer

# This will take a few minutes to:
# 1. Fetch from OER Commons
# 2. Fetch from OpenStax
# 3. Generate embeddings
```

### 8. Generate Embeddings for Search

```bash
# Open Django shell
docker-compose exec web python manage.py shell

# Then run:
from resources.services.ai_utils import generate_embeddings
generate_embeddings()
exit()
```

## Common Issues & Solutions

### Issue 1: Port 8000 Already in Use
```bash
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill the process or change port in docker-compose.yml
```

### Issue 2: Database Connection Failed
```bash
# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Issue 3: Permission Errors (Windows)
```powershell
# Run PowerShell as Administrator
# Or adjust Docker Desktop settings
```

### Issue 4: Out of Memory
- Increase Docker memory to 4GB minimum
- Docker Desktop → Settings → Resources → Memory

## Quick Validation Commands

Run these to verify everything is working:

```bash
# 1. Check all containers are running
docker-compose ps

# 2. Check web logs
docker-compose logs web --tail 50

# 3. Check celery logs
docker-compose logs celery --tail 20

# 4. Test database connection
docker-compose exec web python manage.py dbshell

# 5. Check Django configuration
docker-compose exec web python manage.py check

# 6. Check installed apps
docker-compose exec web python manage.py showmigrations
```

## Success Criteria for Trial Run

- [ ] All 5 containers running (web, db, redis, celery, celery-beat)
- [ ] Web interface accessible at http://localhost:8000
- [ ] Admin panel accessible and can login
- [ ] No errors in web logs
- [ ] Database has pgvector extension installed
- [ ] Can run migrations without errors

## If Everything Works...

You're ready to:
1. ✅ Load sample OER data
2. ✅ Test semantic search
3. ✅ Explore admin interface
4. ✅ Test CSV upload
5. ✅ Configure Talis integration

## If Something Fails...

1. Check logs: `docker-compose logs [service-name]`
2. Check this file for common issues
3. Restart services: `docker-compose restart`
4. Full reset: `docker-compose down -v && docker-compose up --build`

---

**Ready to Launch!** Run: `docker-compose up --build`
