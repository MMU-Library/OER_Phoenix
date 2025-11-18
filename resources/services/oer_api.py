import requests
import logging
import json
from django.db import transaction
from resources.models import OERResource, OERSource
from .ai_utils import generate_embeddings

logger = logging.getLogger(__name__)

OER_SOURCES = [
    {
        'name': 'OER Commons',
        'url': 'https://www.oercommons.org/api/resources',
        'params': {'format': 'json', 'per_page': 50},
        'field_map': {
            'title': 'title',
            'description': 'description',
            'url': 'url',
            'license': 'license'
        }
    },
    {
        'name': 'OpenStax',
        'url': 'https://api.openstax.org/api/v2/resources',
        'params': {'page[size]': 50},
        'field_map': {
            'title': 'attributes.title',
            'description': 'attributes.description',
            'url': 'attributes.url',
            'license': 'attributes.license'
        }
    }
]

def fetch_nested_value(data, key_path):
    keys = key_path.split('.')
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, {})
        else:
            return ''
    return data if isinstance(data, (str, int, float)) else ''

@transaction.atomic
def fetch_oer_resources():
    for source in OER_SOURCES:
        try:
            # Ensure there is an OERSource model instance to attach resources to
            source_obj, created = OERSource.objects.get_or_create(
                name=source.get('name', 'Unknown'),
                defaults={
                    'source_type': 'API',
                    'api_endpoint': source.get('url', ''),
                    'request_params': source.get('params', {}),
                    'request_headers': source.get('headers', {})
                }
            )

            response = requests.get(source['url'], params=source.get('params', {}))
            response.raise_for_status()
            data = response.json()

            # Handle different response structures
            items = data.get('results', []) if 'results' in data else data.get('data', [])
            if not isinstance(items, list) and isinstance(items, dict):
                # Some APIs return a dict with nested list under other keys
                # fall back to wrapping single dict as list
                items = [items]

            processed = 0
            for item in items:
                title = fetch_nested_value(item, source['field_map']['title'])
                url = fetch_nested_value(item, source['field_map']['url'])
                if not title or not url:
                    continue

                resource_data = {
                    'title': title,
                    'description': fetch_nested_value(item, source['field_map']['description']),
                    'url': url,
                    'license': fetch_nested_value(item, source['field_map'].get('license', '')),
                    'source': source_obj
                }

                # Create or update resource (attach the OERSource instance)
                resource, created = OERResource.objects.update_or_create(
                    url=resource_data['url'],
                    defaults={
                        'title': resource_data['title'],
                        'description': resource_data['description'],
                        'license': resource_data['license'],
                        'source': resource_data['source']
                    }
                )
                processed += 1

            logger.info(f"Fetched {processed} resources from {source['name']}")
        except Exception as e:
            logger.exception(f"Error fetching from {source.get('name', source['url'])}: {str(e)}")

    # Generate embeddings after import
    try:
        generate_embeddings()
    except Exception:
        logger.exception("Failed to generate embeddings after import")
