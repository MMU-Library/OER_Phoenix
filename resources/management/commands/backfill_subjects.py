# resources/management/commands/backfill_subjects.py

from django.core.management.base import BaseCommand
from django.db.models import Q

from resources.models import OERResource


class Command(BaseCommand):
    help = (
        "Backfill missing subject values on OERResource using simple heuristics. "
        "Use --dry-run to see how many would be updated."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many records would be updated without saving.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        qs = OERResource.objects.filter(
            Q(subject__isnull=True) | Q(subject__exact="")
        )
        total = qs.count()
        self.stdout.write(f"Found {total} resources with empty subject")

        updated = 0

        for r in qs.iterator(chunk_size=500):
            new_subject = None

            # Example heuristic: reuse resource_type if it looks like a list
            if r.resource_type:
                rt = r.resource_type.strip()
                if ";" in rt or "," in rt:
                    new_subject = rt

            if not new_subject:
                continue

            if dry_run:
                updated += 1
                continue

            r.subject = new_subject[:500]
            r.save(update_fields=["subject"])
            updated += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"[DRY RUN] Would update {updated} records")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Updated {updated} records")
            )
