#!/usr/bin/env python3
"""Run a small CSV harvest test inside the web container.

This script creates a temporary OERSource configured for CSV harvesting,
monkeypatches the `CSVHarvester.request` method to return a small in-memory
CSV payload (so no external network calls are made), runs the harvester, and
prints concise results.

Run with:
  python ./scripts/run_csv_harvest_test.py

"""
import sys
import time
import traceback

import django

django.setup()

from resources.models import OERSource, OERResource, HarvestJob
from resources.harvesters.csv_harvester import CSVHarvester


class FakeResp:
    def __init__(self, content, status_code=200):
        self.content = content
        self.status_code = status_code


def main():
    try:
        # Small CSV content (2 rows)
        fake_csv = "title,url,description\nTest 1,http://example.com/1,Desc1\nTest 2,http://example.com/2,Desc2\n"

        def fake_request(self, method, url, headers=None, params=None, timeout=15, max_attempts=3):
            return FakeResp(fake_csv.encode('utf-8'))

        # Monkeypatch the request method on CSVHarvester
        CSVHarvester.request = fake_request

        # Create a temporary source
        name = f"__test_csv_source__{int(time.time())}"
        src = OERSource.objects.create(
            name=name,
            source_type='CSV',
            csv_url='http://example.test/csv',
            is_active=True,
        )
        print('Created OERSource:', src.id, src.name)

        # Run harvest
        harv = CSVHarvester(src)
        job = harv.harvest()

        # Print concise results
        print('\nHarvest results:')
        print('HarvestJob id:', job.id)
        print('status:', job.status)
        print('resources_found:', job.resources_found)
        print('resources_created:', job.resources_created)
        print('resources_updated:', job.resources_updated)
        print('resources_failed:', job.resources_failed)
        print('\nHarvestJob.log_messages:')
        print(job.log_messages)

        src_count = OERResource.objects.filter(source=src).count()
        print('\nOERResource count for test source:', src_count)
        print('Global OERResource count:', OERResource.objects.count())
        print('Global HarvestJob count:', HarvestJob.objects.count())

        # Note: leaving the test source in DB for inspection; user can remove it later

    except Exception:
        print('Error during CSV harvest test:')
        traceback.print_exc()
        sys.exit(2)


if __name__ == '__main__':
    main()
