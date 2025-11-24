import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oer_rebirth.settings')
# Ensure project root is on sys.path (container may not have it by default)
sys.path.append('/app')
django.setup()

from resources.models import OERSource
from resources.harvesters.marcxml_harvester import MARCXMLHarvester

OAPEN_URL = 'https://memo.oapen.org/file/oapen/OAPENLibrary_MARCXML_books.xml'

def main():
    src, created = OERSource.objects.update_or_create(
        name='OAPEN MARCXML (smoke)',
        defaults={
            'source_type': 'MARCXML',
            'marcxml_url': OAPEN_URL,
            'is_active': True,
            'max_resources_per_harvest': 50,
            'harvest_schedule': 'manual'
        }
    )

    print(f"Using source id={src.id} (created={created}) url={src.marcxml_url}")

    harvester = MARCXMLHarvester(src)
    # run a smoke harvest
    job = harvester.harvest()

    print('Harvest job:', job.id)
    print('Status:', job.status)
    print('Resources found:', job.resources_found)
    print('Resources created:', job.resources_created)
    print('Resources updated:', job.resources_updated)
    print('Resources failed:', job.resources_failed)
    print('Log messages:', job.log_messages)

if __name__ == '__main__':
    main()
