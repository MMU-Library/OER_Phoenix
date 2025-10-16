from django.core.management.base import BaseCommand
from resources.models import Resource
from resources.services.talis_api import create_reading_list

class Command(BaseCommand):
    help = 'Exports selected resources to Talis Reading List'
    
    def add_arguments(self, parser):
        parser.add_argument('--resource-ids', nargs='+', type=int, required=True)
        parser.add_argument('--title', type=str, required=True)
        parser.add_argument('--description', type=str, default='')
    
    def handle(self, *args, **options):
        resources = Resource.objects.filter(id__in=options['resource_ids'])
        list_id = create_reading_list(
            options['title'],
            options['description'],
            resources
        )
        self.stdout.write(self.style.SUCCESS(
            f'Successfully created Talis reading list: {list_id}'
        ))
