from celery import shared_task
from .services.oer_api import fetch_oer_resources
from .services.talis import TalisClient
from .models import OERResource
from .services import ai_utils
from celery.utils.log import get_task_logger
from django.utils import timezone
import requests
from .models import TalisPushJob


logger = get_task_logger(__name__)

def get_resource_embedding(description, title):
    # Example implementation (replace with actual logic)
    return f"{description} {title}"

@shared_task(bind=True, max_retries=3)
def fetch_oer_resources_task(self):
    try:
        # Fetch new OER resources from all active sources
        fetch_oer_resources()
        return "Harvest completed successfully"
    except Exception as e:
        # Retry the task after 30 seconds
        raise self.retry(countdown=30, exc=e)

def generate_embeddings():
    """Generate embeddings for all resources without them"""
    # Filter resources where content_embedding is null
    resources = OERResource.objects.filter(content_embedding__isnull=True)
    
    # Generate embeddings in batches
    for resource in resources:
        embedding = get_resource_embedding(resource.description, resource.title)
        resource.content_embedding = embedding
        resource.save()


@shared_task(bind=True, max_retries=3)
def generate_embedding_for_resource(self, resource_id):
    """Celery task to compute an embedding for a single resource by id."""
    try:
        success = ai_utils.compute_and_store_embedding_for_resource(resource_id)
        return success
    except Exception as e:
        raise self.retry(countdown=30, exc=e)

@shared_task
def export_to_talis(resource_ids, title, description):
    """
    Celery task to export resources to Talis Reading List
    """
    client = TalisClient()
    resources = OERResource.objects.filter(id__in=resource_ids)
    list_id = client.create_reading_list(title, description, resources)
    return f"Successfully created Talis reading list: {list_id}"


@shared_task(bind=True)
def talis_push_report(self, push_job_id):
    """Task: post stored report snapshot to configured Talis API and update job."""
    try:
        job = TalisPushJob.objects.get(id=push_job_id)
    except TalisPushJob.DoesNotExist:
        logger.error(f"TalisPushJob {push_job_id} not found")
        return False

    job.status = 'running'
    job.started_at = timezone.now()
    job.save()

    talis_url = job.target_url
    if not talis_url:
        logger.error(f"TalisPushJob {job.id} missing target_url, aborting push.")
        job.status = 'failed'
        job.completed_at = timezone.now()
        job.response_body = 'Missing Talis API endpoint.'
        job.save()
        return False

    # If token is stored in settings (not on job), fetch from settings
    from django.conf import settings
    talis_token = getattr(settings, 'TALIS_API_TOKEN', None)

    # Build CSV payload
    import csv
    from io import StringIO

    s = StringIO()
    writer = csv.writer(s)
    writer.writerow(['Original Title', 'Original Author', 'Matched Resource ID', 'Matched Title', 'Matched URL', 'Score', 'Source'])
    for item in job.report_snapshot:
        orig = item.get('original', {})
        matches = item.get('matches', [])
        if not matches:
            writer.writerow([orig.get('title', ''), orig.get('author', ''), '', '', '', '', ''])
        else:
            for m in matches:
                writer.writerow([orig.get('title', ''), orig.get('author', ''), m.get('id'), m.get('title'), m.get('url'), m.get('final_score'), m.get('source')])

    payload = s.getvalue().encode('utf-8')
    headers = {'Content-Type': 'text/csv'}
    if talis_token:
        headers['Authorization'] = f'Bearer {talis_token}'

    try:
        resp = requests.post(talis_url, data=payload, headers=headers, timeout=60)
        job.response_code = getattr(resp, 'status_code', None)
        try:
            job.response_body = resp.text
        except Exception:
            job.response_body = ''

        if resp.status_code in (200, 201):
            job.status = 'completed'
        else:
            job.status = 'failed'

    except Exception as e:
        logger.exception('Error pushing to Talis')
        job.status = 'failed'
        job.response_body = str(e)

    job.completed_at = timezone.now()
    job.save()
    return job.status