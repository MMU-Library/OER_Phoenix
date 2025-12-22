from django.core.management.base import BaseCommand
from resources.models import OERResource
from resources.tasks import fetch_and_extract_content


class Command(BaseCommand):
    help = "Fetch and extract content for resources (by id or all)."

    def add_arguments(self, parser):
        parser.add_argument('--resource-id', type=int, help='ID of single resource to process')
        parser.add_argument('--all', action='store_true', help='Process all resources')

    def handle(self, *args, **options):
        rid = options.get('resource_id')
        if rid:
            fetch_and_extract_content.delay(rid)
            self.stdout.write(self.style.SUCCESS(f'Enqueued extraction for resource {rid}'))
            return

        if options.get('all'):
            qs = OERResource.objects.all().only('id')
            count = 0
            for r in qs:
                fetch_and_extract_content.delay(r.id)
                count += 1
            self.stdout.write(self.style.SUCCESS(f'Enqueued extraction for {count} resources'))
            return

        self.stdout.write(self.style.ERROR('Specify --resource-id or --all'))
