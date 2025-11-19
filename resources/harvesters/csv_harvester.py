import csv
import io
import logging
from urllib.parse import urlparse
from resources.harvesters.utils import request_with_retry
from resources.harvesters.base_harvester import BaseHarvester

logger = logging.getLogger(__name__)


class CSVHarvester(BaseHarvester):
    def __init__(self, source):
        super().__init__(source)
        self.config = self._get_config()

    def _get_config(self):
        return {
            'csv_url': getattr(self.source, 'api_endpoint', None) or getattr(self.source, 'csv_url', None),
            'headers': getattr(self.source, 'request_headers', {}) or {},
            'params': getattr(self.source, 'request_params', {}) or {}
        }

    def test_connection(self):
        cfg = self._get_config()
        try:
            resp = request_with_retry('get', cfg['csv_url'], headers=cfg.get('headers', {}), timeout=10, max_attempts=3)
            if resp.status_code != 200:
                logger.warning('CSV test connection returned status %s for %s', resp.status_code, cfg['csv_url'])
            return resp.status_code == 200
        except Exception:
            return False

    def _flexible_csv_reader(self, content):
        # Try to sniff dialect, fallback to excel
        try:
            sample = content[:8192]
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)
        except Exception:
            dialect = csv.excel
        text_io = io.StringIO(content)
        reader = csv.DictReader(text_io, dialect=dialect)
        return list(reader)

    def fetch_and_process_records(self):
        cfg = self._get_config()
        url = cfg['csv_url']
        headers = cfg.get('headers', {}) or {}
        params = cfg.get('params', {}) or {}

        try:
            resp = self.request('get', url, headers=headers, params=params, timeout=30, max_attempts=4)
        except Exception as e:
            logger.error(f"CSV fetch failed: {e}")
            raise

        try:
            # decode content
            content = resp.content.decode('utf-8', errors='replace')
            rows = self._flexible_csv_reader(content)
        except Exception as e:
            # Log helpful debug info: status and content-type
            ct = ''
            try:
                ct = resp.headers.get('content-type', '')
            except Exception:
                pass
            logger.error(f"CSV parse failed: {e}; status=%s; content-type=%s; url=%s", getattr(resp, 'status_code', None), ct, url)
            raise

        records = []
        for r in rows:
            # best-effort mapping
            title = r.get('title') or r.get('name') or r.get('Title')
            url = r.get('url') or r.get('link') or r.get('URL') or r.get('identifier')
            desc = r.get('description') or r.get('summary')
            if not title and not url:
                continue
            records.append({'title': title, 'url': url, 'description': desc})

        return records
