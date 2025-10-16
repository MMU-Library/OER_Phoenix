import requests
from django.db import transaction
from resources.models import OERResource  
from .ai_utils import generate_embeddings

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
        data = data.get(key, {})
    return data if isinstance(data, str) else ''

@transaction.atomic
def fetch_oer_resources():
    for source in OER_SOURCES:
        try:
            response = requests.get(source['url'], params=source.get('params', {}))
            response.raise_for_status()
            data = response.json()
            
            # Handle different response structures
            items = data.get('results', []) if 'results' in data else data.get('data', [])
            
            for item in items:
                resource_data = {
                    'title': fetch_nested_value(item, source['field_map']['title']),
                    'description': fetch_nested_value(item, source['field_map']['description']),
                    'url': fetch_nested_value(item, source['field_map']['url']),
                    'license': fetch_nested_value(item, source['field_map'].get('license', '')),
                    'source': source['name']
                }
                
                # Create or update resource
                resource, created = OERResource.objects.update_or_create(
                    url=resource_data['url'],
                    defaults=resource_data
                )
                
            print(f"Fetched {len(items)} resources from {source['name']}")
        except Exception as e:
            print(f"Error fetching from {source['name']}: {str(e)}")
    
    # Generate embeddings after import
    generate_embeddings()
