#!/usr/bin/env python3
"""Probe DOAB API endpoint and print response headers and a content snippet."""
import sys
import traceback
import requests
from resources.harvesters.preset_configs import PRESET_CONFIGS

def main():
    try:
        p = PRESET_CONFIGS['API']['doab']
        url = p['api_endpoint']
        params = p.get('request_params', {})
        print('URL:', url)
        print('Params:', params)
        r = requests.get(url, params=params, timeout=15)
        print('Status:', r.status_code)
        print('Content-Type:', r.headers.get('content-type'))
        print('Len:', len(r.content))
        print('Start (first 800 chars):')
        print(r.text[:800])
    except Exception:
        traceback.print_exc()
        return 2
    return 0

if __name__ == '__main__':
    sys.exit(main())
