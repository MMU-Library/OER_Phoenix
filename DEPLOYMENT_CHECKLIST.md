# Open Educational Resourcer - Deployment Checklist

Use this checklist to ensure proper deployment of the OER platform.

## Pre-Deployment Checklist

### Environment Configuration

- [ ] Copy `.env.example` to `.env`
- [ ] Update `DJANGO_SECRET_KEY` with strong random key
  ```bash
  python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
  ```
- [ ] Set `DJANGO_DEBUG=False` for production
- [ ] Configure `DJANGO_ALLOWED_HOSTS` with your domain(s)
- [ ] Set strong database credentials (change from defaults)
- [ ] Configure `DB_HOST` to point to production database
- [ ] Review all environment variables

### Security

- [ ] Change default admin password
- [ ] Enable HTTPS/SSL
- [ ] Configure CSRF trusted origins if needed
- [ ] Review CORS settings if using API
- [ ] Set up firewall rules
- [ ] Enable security headers
- [ ] Configure rate limiting
- [ ] Review file upload size limits

### Database

- [ ] PostgreSQL 14+ installed with pgvector extension
- [ ] Database created with proper encoding (UTF-8)
- [ ] Database user created with appropriate permissions
- [ ] Connection pooling configured (if applicable)
- [ ] Backup strategy implemented
- [ ] Monitoring enabled

### Docker Configuration

- [ ] Review resource limits in docker-compose.yml
- [ ] Configure restart policies (restart: always)
- [ ] Set up log rotation
- [ ] Configure health checks
- [ ] Review volume mounts
- [ ] Set appropriate user permissions

### Talis Integration (Optional)

- [ ] Obtain Talis API credentials
- [ ] Set `TALIS_TENANT` in .env
- [ ] Set `TALIS_CLIENT_ID` in .env
- [ ] Set `TALIS_CLIENT_SECRET` in .env
- [ ] Test authentication flow
- [ ] Verify reading list creation permissions

## Deployment Steps

### 1. Initial Setup

```bash
# Clone repository
[ ] git clone <repository-url>
[ ] cd oer_rebirth

# Configure environment
[ ] cp .env.example .env
[ ] nano .env  # Edit configuration

# Make scripts executable (Linux/Mac)
[ ] chmod +x docker-entrypoint.sh setup.sh
```

### 2. Build and Start Services

```bash
# Build containers
[ ] docker-compose build

# Start services
[ ] docker-compose up -d

# Check service status
[ ] docker-compose ps
[ ] docker-compose logs
```

### 3. Database Setup

```bash
# Run migrations
[ ] docker-compose exec web python manage.py migrate

# Create superuser
[ ] docker-compose exec web python manage.py createsuperuser

# Verify database connection
[ ] docker-compose exec db psql -U postgres -d oer_rebirth -c "SELECT version();"
```

### 4. Load Initial Data

```bash
# Fetch OER resources
[ ] docker-compose exec web python manage.py fetch_oer

# Generate embeddings
[ ] docker-compose exec web python manage.py shell
    >>> from resources.services.ai_utils import generate_embeddings
    >>> generate_embeddings()
    >>> exit()

# Verify data loaded
[ ] docker-compose exec db psql -U postgres -d oer_rebirth -c "SELECT COUNT(*) FROM resources_oerresource;"
```

### 5. Static Files (Production)

```bash
# Collect static files
[ ] docker-compose exec web python manage.py collectstatic --noinput

# Verify static files served correctly
[ ] curl http://localhost:8000/static/
```

### 6. Celery Configuration

```bash
# Check celery worker status
[ ] docker-compose logs celery

# Check celery beat status
[ ] docker-compose logs celery-beat

# Test a celery task
[ ] docker-compose exec web python manage.py shell
    >>> from resources.tasks import fetch_oer_resources_task
    >>> result = fetch_oer_resources_task.delay()
    >>> result.status
```

## Post-Deployment Verification

### Functionality Tests

- [ ] Homepage loads correctly
- [ ] Admin panel accessible at /admin
- [ ] Can log in with superuser credentials
- [ ] AI search returns results
- [ ] CSV upload works
- [ ] Resource comparison functions
- [ ] Talis export initiates (if configured)
- [ ] Celery tasks execute

### Performance Tests

- [ ] Page load times acceptable
- [ ] Search response time < 2 seconds
- [ ] Database queries optimized
- [ ] No memory leaks after extended use
- [ ] Celery processes tasks without backup

### Security Tests

- [ ] HTTPS redirects working
- [ ] CSRF protection active
- [ ] Admin panel requires authentication
- [ ] No debug information exposed
- [ ] File upload restrictions enforced
- [ ] SQL injection prevented
- [ ] XSS protection active

## Monitoring Setup

### Application Monitoring

- [ ] Set up error tracking (Sentry, Rollbar)
- [ ] Configure logging aggregation
- [ ] Set up uptime monitoring
- [ ] Configure performance monitoring
- [ ] Set up alerting for errors

### Infrastructure Monitoring

- [ ] Monitor container health
- [ ] Track CPU/memory usage
- [ ] Monitor disk space
- [ ] Track database performance
- [ ] Monitor Redis memory
- [ ] Set up backup verification

### Metrics to Track

- [ ] Response time by endpoint
- [ ] Database query performance
- [ ] Search accuracy/relevance
- [ ] API rate limits
- [ ] User activity
- [ ] Error rates
- [ ] Resource usage trends

## Backup Configuration

### Database Backups

```bash
# Manual backup
[ ] docker-compose exec db pg_dump -U postgres oer_rebirth > backup.sql

# Set up automated backups
[ ] Configure cron job or scheduled task
[ ] Test restore procedure
[ ] Store backups off-site
[ ] Set retention policy
```

### Application Backups

- [ ] Backup .env file (securely)
- [ ] Backup uploaded files
- [ ] Backup custom templates
- [ ] Backup static files
- [ ] Document restore procedure

## Maintenance Plan

### Regular Tasks

#### Daily
- [ ] Check error logs
- [ ] Monitor system resources
- [ ] Review backup success

#### Weekly
- [ ] Update OER resources (run fetch_oer)
- [ ] Regenerate embeddings if needed
- [ ] Review user activity
- [ ] Check disk space

#### Monthly
- [ ] Update dependencies
- [ ] Review and update security settings
- [ ] Test backup restoration
- [ ] Review monitoring alerts
- [ ] Update documentation

#### Quarterly
- [ ] Major version updates
- [ ] Security audit
- [ ] Performance optimization
- [ ] User feedback review

## Scaling Considerations

### Horizontal Scaling

- [ ] Set up load balancer
- [ ] Configure session storage (Redis)
- [ ] Set up read replicas for database
- [ ] Configure Celery with multiple workers
- [ ] Implement caching strategy

### Vertical Scaling

- [ ] Increase container resources
- [ ] Optimize database queries
- [ ] Add database indexes
- [ ] Configure connection pooling
- [ ] Optimize AI model loading

## Rollback Plan

### If Deployment Fails

```bash
# Stop services
[ ] docker-compose down

# Restore previous version
[ ] git checkout <previous-commit>
[ ] docker-compose build
[ ] docker-compose up -d

# Restore database
[ ] docker-compose exec db psql -U postgres oer_rebirth < backup.sql

# Verify functionality
[ ] Run test suite
[ ] Check critical endpoints
```

### Rollback Checklist

- [ ] Document reason for rollback
- [ ] Notify stakeholders
- [ ] Restore from last known good backup
- [ ] Verify all services running
- [ ] Test critical functionality
- [ ] Monitor for issues
- [ ] Plan fixes for next deployment

## Documentation

### Required Documentation

- [ ] Deployment procedure documented
- [ ] Configuration options documented
- [ ] API endpoints documented (if applicable)
- [ ] Troubleshooting guide created
- [ ] Backup/restore procedures documented
- [ ] Monitoring setup documented
- [ ] Maintenance schedule documented

### User Documentation

- [ ] User guide for search functionality
- [ ] CSV upload instructions
- [ ] Talis export workflow
- [ ] FAQ document
- [ ] Contact information for support

## Production Environment Variables

```bash
# Django Settings
DJANGO_SECRET_KEY=<generate-new-secret-key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DJANGO_SECURE_SSL_REDIRECT=True

# Database
DB_NAME=oer_rebirth
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Celery/Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Talis (Optional)
TALIS_TENANT=your-tenant
TALIS_CLIENT_ID=your-client-id
TALIS_CLIENT_SECRET=your-client-secret

# Monitoring (Optional)
SENTRY_DSN=your-sentry-dsn
```

## Common Issues and Solutions

### Issue: Container won't start
- Check logs: `docker-compose logs`
- Verify .env configuration
- Check port conflicts
- Verify Docker resources

### Issue: Database connection failed
- Verify database service running
- Check credentials in .env
- Test connection manually
- Review network configuration

### Issue: Search not working
- Verify embeddings generated
- Check AI model loaded
- Review vector store initialization
- Check resource count in database

### Issue: Celery tasks stuck
- Check Redis connection
- Restart Celery workers
- Review task queue
- Check worker logs

## Final Verification

- [ ] All services running
- [ ] No errors in logs
- [ ] All tests passing
- [ ] Monitoring active
- [ ] Backups configured
- [ ] Documentation complete
- [ ] Team trained on deployment
- [ ] Rollback plan tested
- [ ] Support contacts documented
- [ ] Go-live approved

## Sign-off

- [ ] Developer sign-off
- [ ] Operations sign-off
- [ ] Security sign-off
- [ ] Stakeholder approval

**Deployment Date**: _______________
**Deployed By**: _______________
**Version**: _______________

---

**Note**: Keep this checklist updated as your deployment process evolves.
