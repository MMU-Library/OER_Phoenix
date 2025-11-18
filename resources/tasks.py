from celery import shared_task
from .services.oer_api import fetch_oer_resources
from .services.talis import TalisClient
from .models import OERResource

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

@shared_task
def export_to_talis(resource_ids, title, description):
    """
    Celery task to export resources to Talis Reading List
    """
    client = TalisClient()
    resources = OERResource.objects.filter(id__in=resource_ids)
    list_id = client.create_reading_list(title, description, resources)
    return f"Successfully created Talis reading list: {list_id}"