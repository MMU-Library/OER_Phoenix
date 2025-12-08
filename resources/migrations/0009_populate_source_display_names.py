# resources/migrations/0009_populate_source_display_names.py
from django.db import migrations


def populate_display_names(apps, schema_editor):
    """
    Populate user-friendly display names for existing OER sources
    based on current naming patterns observed in the system
    """
    OERSource = apps.get_model('resources', 'OERSource')
    
    # Mapping of current technical names to user-friendly display names
    name_mapping = {
        # OAPEN variants
        'OAPEN MARCXML dump': 'OAPEN Open Access Books',
        'OAPEN Library - OAIPMH': 'OAPEN Library Collection',
        'OAPEN MARCXML (correct link)': 'OAPEN Books (Direct Links)',
        'OAPEN REST API (Books)': 'OAPEN API Collection',
        'OAPEN MARCXML (smoke)': 'OAPEN Test Collection',
        
        # DOAB variants
        'DOAB OAI-PMH': 'Directory of Open Access Books',
        'DOAB OAI-PMH (Preset update check)': 'DOAB (Auto-Update)',
        
        # Other sources
        'OER Commons CSV': 'OER Commons',
        'Skills Commons OER': 'Skills Commons',
        'OpenStax': 'OpenStax Textbooks',
        'MIT OpenCourseWare': 'MIT OpenCourseWare',
        'Open Textbook Library': 'Open Textbook Library',
    }
    
    # Apply mappings
    updated_sources = []
    for old_name, new_display_name in name_mapping.items():
        updated_count = OERSource.objects.filter(name=old_name).update(
            display_name=new_display_name
        )
        if updated_count > 0:
            updated_sources.append(f"✓ Updated '{old_name}' → '{new_display_name}'")
    
    # For any sources without a display_name, copy the name as a fallback
    sources_without_display = OERSource.objects.filter(display_name='')
    for source in sources_without_display:
        # Clean up common technical suffixes/prefixes for better display
        clean_name = source.name
        
        # Remove common technical patterns
        replacements = [
            (' - OAIPMH', ''),
            (' OAI-PMH', ''),
            (' MARCXML dump', ' Collection'),
            (' (correct link)', ''),
            (' REST API', ' API'),
        ]
        
        for old, new in replacements:
            clean_name = clean_name.replace(old, new)
        
        source.display_name = clean_name
        source.save()
        updated_sources.append(f"→ Auto-generated display name for '{source.name}': '{clean_name}'")
    
    if updated_sources:
        print("\n".join(updated_sources))


def reverse_populate_display_names(apps, schema_editor):
    """
    Reverse migration: clear all display names
    """
    OERSource = apps.get_model('resources', 'OERSource')
    OERSource.objects.all().update(display_name='')


class Migration(migrations.Migration):
    """
    Data migration to populate display_name field for existing OERSource records
    """
    
    dependencies = [
        ('resources', '0008_add_display_name_and_translation_fields'),  # Update this to match your actual schema migration
    ]
    
    operations = [
        migrations.RunPython(
            populate_display_names,
            reverse_code=reverse_populate_display_names
        ),
    ]
