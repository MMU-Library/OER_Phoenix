from celery import shared_task
from .services.oer_api import fetch_oer_resources
from .services.talis import TalisClient
from .models import OERResource

@shared_task
def fetch_oer_resources_task():
    """
    Celery task to fetch OER resources from external APIs
    """
    fetch_oer_resources()
    return "OER resources fetched successfully"

@shared_task
def export_to_talis(resource_ids, title, description):
    """
    Celery task to export resources to Talis Reading List
    """
    client = TalisClient()
    resources = OERResource.objects.filter(id__in=resource_ids)
    list_id = client.create_reading_list(title, description, resources)
    return f"Successfully created Talis reading list: {list_id}"
