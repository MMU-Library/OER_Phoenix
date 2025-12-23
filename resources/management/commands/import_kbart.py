from django.core.management.base import BaseCommand, CommandError

from resources.models import OERSource
from resources.harvesters.kbart_harvester import KBARTHarvester


class Command(BaseCommand):
    help = "Import a KBART (TSV) file and create OERResources for a given source."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path or URL to KBART TSV file")
        parser.add_argument("source_name", help="Name of the OERSource to attach resources to")
        parser.add_argument("--create-if-missing", action="store_true", help="Create the OERSource if it does not exist")

    def handle(self, *args, **options):
        path = options["path"]
        source_name = options["source_name"]
        create_if_missing = options["create_if_missing"]

        try:
            source = OERSource.objects.get(name=source_name)
        except OERSource.DoesNotExist:
            if create_if_missing:
                source = OERSource.objects.create(name=source_name, display_name=source_name, source_type="CSV")
                self.stdout.write(self.style.SUCCESS(f"Created OERSource '{source_name}'"))
            else:
                raise CommandError(f"OERSource '{source_name}' not found. Use --create-if-missing to create it.")

        harvester = KBARTHarvester()
        self.stdout.write(f"Harvesting KBART from {path} into source '{source.get_display_name()}'...")
        job = harvester.harvest_from_path(source, path)
        self.stdout.write(self.style.SUCCESS(f"Harvest complete: created={job.resources_created} updated={job.resources_updated} failed={job.resources_failed}"))
