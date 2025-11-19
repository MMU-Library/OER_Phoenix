#!/usr/bin/env python3
"""Create sources from DOAB and OAPEN presets and run small harvests for each.

This script will:
 - Create a temporary OERSource from the preset (API and OAIPMH where available)
 - Set a small `max_resources_per_harvest` to avoid large runs
 - Run the appropriate harvester and print concise results

Run inside the web container with DJANGO_SETTINGS_MODULE set.
"""
import sys
import traceback
import time
import django

django.setup()

from resources.harvesters.preset_configs import PRESET_CONFIGS
from resources.models import OERSource, HarvestJob, OERResource

def create_from_preset(source_type, key, limit=5):
    preset = PRESET_CONFIGS.get(source_type, {}).get(key)
    if not preset:
        print('Preset not found:', source_type, key)
        return None

    name = f"__preset_test__{preset['name']}__{int(time.time())}"
    fields = {
        'name': name,
        'description': preset.get('description',''),
        'source_type': source_type,
        'is_active': True,
        'harvest_schedule': preset.get('harvest_schedule','manual'),
        'max_resources_per_harvest': limit,
    }
    # Copy known URL fields
    for fld in ('api_endpoint','oaipmh_url','csv_url'):
        if preset.get(fld):
            fields[fld] = preset.get(fld)

    # JSON fields
    fields['request_params'] = preset.get('request_params', {})
    fields['request_headers'] = preset.get('request_headers', {})

    src = OERSource.objects.create(**fields)
    print('Created source:', src.id, src.name)
    return src

def run_harvest_for_source(src):
    try:
        from resources.harvesters.api_harvester import APIHarvester
        from resources.harvesters.oaipmh_harvester import OAIHarvester
        from resources.harvesters.csv_harvester import CSVHarvester

        if src.source_type == 'API':
            harv = APIHarvester(src)
        elif src.source_type == 'OAIPMH':
            harv = OAIHarvester(src)
        elif src.source_type == 'CSV':
            harv = CSVHarvester(src)
        else:
            print('Unknown source type for', src.id)
            return None

        job = harv.harvest()
        print('Job', job.id, job.status, 'found', job.resources_found, 'created', job.resources_created)
        return job
    except Exception:
        traceback.print_exc()
        return None

def main():
    tests = [
        ('API','oapen'),
        ('API','doab'),
        ('OAIPMH','oapen'),
        ('OAIPMH','doab')
    ]

    created = []
    for stype, key in tests:
        try:
            print('\n=== Testing preset', stype, key, '===')
            src = create_from_preset(stype, key, limit=5)
            if src:
                created.append(src)
                job = run_harvest_for_source(src)
                time.sleep(1)
        except Exception:
            traceback.print_exc()

    print('\nDone. Created sources:', [s.id for s in created])
    print('You can inspect these in the admin UI and delete them when finished.')

if __name__ == '__main__':
    main()
