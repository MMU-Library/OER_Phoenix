import requests
import logging
import time
from resources.harvesters.utils import request_with_retry
from resources.harvesters.base_harvester import BaseHarvester
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class APIHarvester(BaseHarvester):
    def __init__(self, source):
        super().__init__(source)
        self.config = self._get_config()

    def _get_config(self):
        """Extract configuration from source model"""
        return {
            'base_url': getattr(self.source, 'api_endpoint', None),
            'api_key': getattr(self.source, 'api_key', None),
            'headers': getattr(self.source, 'request_headers', {}) or {},
            'params': getattr(self.source, 'request_params', {}) or {}
        }

    def test_connection(self):
        """Test connection to API endpoint"""
        try:
            config = self._get_config()
            # Test with a simple request
            test_url = f"{config['base_url']}"
            if '?' not in test_url:
                test_url += '?limit=1'

            headers = config.get('headers', {})
            params = config.get('params', {})

            try:
                resp = self.request('get', test_url, headers=headers, params=params, timeout=10, max_attempts=3)
                return resp.status_code == 200
            except Exception as e:
                logger.warning(f"API connection test failed after retries: {e}")
                return False
        except Exception as e:
            logger.error(f"API connection test failed: {str(e)}")
            return False

    def fetch_and_process_records(self):
        """Fetch and process records from API"""
        try:
            config = self._get_config()

            # Build the request
            url = config['base_url']
            headers = config.get('headers', {})
            params = config.get('params', {})

            # Add API key if provided
            if config.get('api_key'):
                if 'Authorization' not in headers:
                    headers['Authorization'] = f"Bearer {config['api_key']}"

            logger.info(f"Fetching API records from: {url}")
            try:
                response = self.request('get', url, headers=headers, params=params, timeout=30, max_attempts=4)
            except Exception as e:
                logger.error(f"API fetch failed after retries: {e}")
                raise ValidationError("API fetch failed after retries") from e

            data = response.json()
            return self._process_api_response(data)

        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            raise ValidationError(f"API request failed: {str(e)}") from e

    def _process_api_response(self, data):
        """Process API response into OER resource data"""
        processed_records = []

        # Handle different API response structures
        if isinstance(data, list):
            records = data
        else:
            # safe-get keys that commonly contain lists
            records = data.get('results') or data.get('items') or data.get('data') or data.get('records')
            if records is None:
                # If there's no list container, treat the whole payload as a single record
                records = [data] if isinstance(data, dict) and data else []

        for record in records:
            try:
                # Map common API fields to OER resource model
                # Some APIs return primitive values inside lists; ensure `record` is a dict
                if not isinstance(record, dict):
                    continue

                resource_data = {
                    'title': record.get('title', record.get('name', '')),
                    'description': record.get('description', record.get('summary', '')),
                    'url': record.get('url', record.get('link', record.get('identifier', ''))),
                    'license': record.get('license', record.get('rights', '')),
                    'publisher': record.get('publisher', record.get('provider', '')),
                    'author': record.get('author', record.get('creator', record.get('owner', ''))),
                    'language': record.get('language', 'en'),
                    'resource_type': record.get('resource_type', record.get('type', '')),
                    'subject': record.get('subject', record.get('category', ''))
                }

                # Require at least title and URL
                if resource_data['title'] and resource_data['url']:
                    processed_records.append(resource_data)

            except Exception as e:
                logger.warning(f"Failed to process API record: {str(e)}")
                continue

        logger.info(f"Processed {len(processed_records)} records from API")
        return processed_records