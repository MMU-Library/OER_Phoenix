#!/usr/bin/env python3
"""Run harvest for an existing OERSource id and print results.

Usage: python ./scripts/run_harvest_for_source.py <source_id>
"""
import sys
import traceback
import django

django.setup()

from resources.models import OERSource

def main():
    if len(sys.argv) < 2:
        print('Usage: run_harvest_for_source.py <source_id>')
        return 2
    sid = int(sys.argv[1])
    try:
        src = OERSource.objects.get(pk=sid)
        print('Running harvest for source', src.id, src.name, src.source_type)
        if src.source_type == 'API':
            from resources.harvesters.api_harvester import APIHarvester as Harv
        elif src.source_type == 'OAIPMH':
            from resources.harvesters.oaipmh_harvester import OAIHarvester as Harv
        elif src.source_type == 'CSV':
            from resources.harvesters.csv_harvester import CSVHarvester as Harv
        else:
            print('Unknown source type:', src.source_type)
            return 3

        harv = Harv(src)
        job = harv.harvest()
        print('Job', job.id, job.status, job.resources_found, job.resources_created, job.resources_failed)
        return 0
    except Exception:
        traceback.print_exc()
        return 4

if __name__ == '__main__':
    sys.exit(main())
