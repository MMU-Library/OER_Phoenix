# resources/management/commands/enrich_subjects.py
from django.core.management.base import BaseCommand
from resources.models import OERResource
from resources.services.subject_enrichment import suggest_subjects_for_resource

class Command(BaseCommand):
    help = "Enrich resources with AI-generated primary subjects where missing."

    def handle(self, *args, **options):
        qs = OERResource.objects.filter(primary_subject="")
        updated = 0
        for r in qs.iterator():
            suggestions = suggest_subjects_for_resource(r)
            if not suggestions:
                continue
            r.ai_subjects = suggestions
            if not r.primary_subject:
                r.primary_subject = suggestions[0]
            r.save(update_fields=["ai_subjects", "primary_subject"])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"Updated {updated} resources with AI subjects"))
