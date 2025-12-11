# resources/management/commands/normalise_resource_types.py

from django.core.management.base import BaseCommand
from resources.models import OERResource

class Command(BaseCommand):
    help = "Normalise resource types into OERResource.normalised_type"

    def handle(self, *args, **options):
        updated = 0
        for r in OERResource.objects.all().iterator():
            raw = (r.resource_type or "").lower()
            title = (r.title or "").lower()

            t = ""
            if "chapter" in raw or "chapter" in title:
                t = "chapter"
            elif "book" in raw or "textbook" in raw:
                t = "book"
            elif "article" in raw or "journal" in raw:
                t = "article"
            # fallback to other
            if not t and raw:
                t = "other"

            if t and r.normalised_type != t:
                r.normalised_type = t
                r.save(update_fields=["normalised_type"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Updated {updated} resources"))
