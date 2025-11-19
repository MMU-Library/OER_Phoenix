#!/usr/bin/env python3
"""Probe OAI-PMH endpoint for a given source id and print basic response info."""
import sys
import traceback
import django

django.setup()

from resources.models import OERSource
import requests

def main(source_id):
    try:
        s = OERSource.objects.get(pk=source_id)
        url = s.oaipmh_url or s.api_endpoint or s.csv_url
        if not url:
            print('No URL configured for source', source_id)
            return 2
        probe = url if url.endswith('?') else url + '?verb=Identify'
        print('Probing', probe)
        r = requests.get(probe, timeout=8)
        print('status_code:', r.status_code)
        print('content_len:', len(r.content))
        print('content_start:', r.content[:400])
        return 0
    except Exception:
        traceback.print_exc()
        return 3

if __name__ == '__main__':
    sid = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    sys.exit(main(sid))
