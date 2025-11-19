import logging
from xml.etree import ElementTree as ET
import time
from urllib.parse import urlencode
from resources.harvesters.utils import request_with_retry
from resources.harvesters.base_harvester import BaseHarvester
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class OAIHarvester(BaseHarvester):
    def __init__(self, source):
        super().__init__(source)
        self.config = self._get_config()

    def _get_config(self):
        # Prefer explicit `oaipmh_url` field; fall back to other common names
        return {
            'base_url': getattr(self.source, 'oaipmh_url', None) or getattr(self.source, 'api_endpoint', None) or getattr(self.source, 'api_url', None) or getattr(self.source, 'oai_endpoint', None),
            'metadata_prefix': (getattr(self.source, 'request_params', {}) or {}).get('metadataPrefix', 'oai_dc'),
            'headers': getattr(self.source, 'request_headers', {}) or {},
            'params': getattr(self.source, 'request_params', {}) or {}
        }

    def test_connection(self):
        config = self._get_config()
        try:
            url = f"{config['base_url']}?verb=Identify"
            resp = request_with_retry('get', url, headers=config.get('headers', {}), timeout=10, max_attempts=3)
            return resp.status_code == 200
        except Exception:
            return False

    def _parse_record(self, record_xml):
        # Use dc namespace where available, fall back to text searches
        title = None
        identifiers = []
        description = None
        for elem in record_xml.findall('.//{http://purl.org/dc/elements/1.1/}title'):
            if elem.text:
                title = elem.text
                break
        if not title:
            # try any title-like tag
            t = record_xml.find('.//title')
            if t is not None and t.text:
                title = t.text

        for elem in record_xml.findall('.//{http://purl.org/dc/elements/1.1/}identifier'):
            if elem.text:
                identifiers.append(elem.text)
        if not identifiers:
            # try any identifier-like tag
            for elem in record_xml.findall('.//identifier'):
                if elem.text:
                    identifiers.append(elem.text)

        for elem in record_xml.findall('.//{http://purl.org/dc/elements/1.1/}description'):
            if elem.text:
                description = elem.text
                break
        if not description:
            d = record_xml.find('.//description')
            if d is not None and d.text:
                description = d.text

        url = identifiers[0] if identifiers else None
        return {
            'title': title,
            'url': url,
            'description': description
        }

    def fetch_and_process_records(self):
        config = self._get_config()
        base = config['base_url']
        metadata_prefix = config.get('metadata_prefix', 'oai_dc')
        params = config.get('params', {}) or {}

        records = []
        resumption_token = None
        while True:
            query_params = {}
            if resumption_token:
                query_params['verb'] = 'ListRecords'
                query_params['resumptionToken'] = resumption_token
            else:
                query_params = {'verb': 'ListRecords', 'metadataPrefix': metadata_prefix}
                query_params.update(params)

            url = f"{base}?{urlencode(query_params)}"
            try:
                resp = self.request('get', url, headers=config.get('headers', {}), timeout=30, max_attempts=4)
            except Exception as e:
                logger.error(f"Failed to fetch OAI-PMH records: {e}")
                raise ValidationError(f"Failed to fetch OAI-PMH records: {e}") from e

            try:
                content = resp.content

                # If the response is HTML or contains wrapping, try to extract the OAI-PMH XML block
                ct = ''
                try:
                    ct = resp.headers.get('content-type', '')
                except Exception:
                    pass

                if isinstance(content, (bytes, bytearray)):
                    lower = content.lower()
                    if b'<html' in lower or b'<!doctype html' in lower or 'html' in ct.lower():
                        # attempt to extract the OAI-PMH XML fragment
                        start = content.find(b'<OAI-PMH')
                        end = content.rfind(b'</OAI-PMH>')
                        if start != -1 and end != -1:
                            content = content[start:end+10]
                        else:
                            logger.error('Non-XML/HTML OAI response received; aborting parse')
                            raise ValidationError('Non-XML response received from OAI endpoint')

                root = ET.fromstring(content)
            except Exception as e:
                logger.error(f"Failed to parse OAI response XML: {e}")
                raise ValidationError(f"Failed to parse OAI response XML: {e}") from e

            for rec in root.findall('.//{http://www.openarchives.org/OAI/2.0/}record'):
                try:
                    parsed = self._parse_record(rec)
                    if parsed.get('url') or parsed.get('title'):
                        records.append(parsed)
                except Exception:
                    logger.exception('Failed to parse record')

            # look for resumptionToken
            rt = root.find('.//{http://www.openarchives.org/OAI/2.0/}resumptionToken')
            if rt is None or (rt.text is None or rt.text.strip() == ''):
                break
            resumption_token = rt.text

        return records


# Backwards compatibility: some code/tests expect `OAIPMHHarvester`
OAIPMHHarvester = OAIHarvester