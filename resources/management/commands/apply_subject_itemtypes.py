from django.core.management.base import BaseCommand
from resources.models import OERResource


class Command(BaseCommand):
    help = "Backfill subject and resource_type for existing OER resources."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many records would be updated without saving.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        updated = 0

        qs = OERResource.objects.all()

        for r in qs:
            changed = False

            # SUBJECT INFERENCE (simple, conservative heuristics)
            if not r.subject:
                # 1) Use keywords if present
                if getattr(r, "keywords", None):
                    r.subject = r.keywords[:255] if isinstance(r.keywords, str) else str(r.keywords)[:255]
                    changed = True

                # 2) Fallback: use level to hint at subject area
                elif getattr(r, "level", None):
                    r.subject = f"General ({r.level})"[:255]
                    changed = True

            # RESOURCE TYPE NORMALISATION
            if not r.resource_type:
                # 1) Infer from format if available
                fmt = getattr(r, "format", "") or ""
                fmt_lower = fmt.lower()

                if "video" in fmt_lower:
                    r.resource_type = "Video"
                    changed = True
                elif "audio" in fmt_lower or "podcast" in fmt_lower:
                    r.resource_type = "Audio"
                    changed = True
                elif "pdf" in fmt_lower or "application/pdf" in fmt_lower:
                    r.resource_type = "Document"
                    changed = True
                elif "html" in fmt_lower or "text/html" in fmt_lower:
                    r.resource_type = "Web page"
                    changed = True

                # 2) Fallback if still empty
                if not r.resource_type:
                    r.resource_type = "Unknown"
                    changed = True

            if changed:
                updated += 1
                if not dry_run:
                    r.save()

        if dry_run:
            self.stdout.write(self.style.WARNING(f"[DRY RUN] Would update {updated} resources."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated {updated} resources."))
