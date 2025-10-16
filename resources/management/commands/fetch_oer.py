from django.core.management.base import BaseCommand
from resources.services.oer_api import fetch_oer_resources
from resources.models import OERResource

class Command(BaseCommand):
    help = 'Fetch OER resources from external APIs'

    def handle(self, *args, **kwargs):
        resources = fetch_oer_resources()
        added = 0
        for data in resources:
            if not OERResource.objects.filter(url=data['url']).exists():
                OERResource.objects.create(
                    title=data['title'],
                    source=data.get('source', 'Unknown'),
                    description=data['description'],
                    license=data.get('license', ''),
                    url=data['url'],
                )
                added += 1
        self.stdout.write(self.style.SUCCESS(f'{added} OER resources fetched and saved.'))
