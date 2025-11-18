import requests
import logging
from django.core.exceptions import ValidationError
from django.utils import timezone
from resources.models import HarvestJob, OERResource

logger = logging.getLogger(__name__)

class APIHarvester:
    def __init__(self, source):
        self.source = source
        self.config = self._get_config()

    def _get_config(self):
        """Extract configuration from source model"""
        return {
            'base_url': self.source.api_endpoint,
            'api_key': self.source.api_key,
            'headers': self.source.request_headers,
            'params': self.source.request_params
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
            
            response = requests.get(
                test_url,
                headers=headers,
                params=params,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"API connection test failed: {str(e)}")
            return False

    def harvest(self):
        """Main harvesting method that returns a HarvestJob"""
        # Create harvest job
        harvest_job = HarvestJob.objects.create(
            source=self.source,
            status='running',
            started_at=timezone.now()
        )
        
        try:
            # Fetch and process records
            records = self.fetch_and_process_records()
            
            # Create OER resources
            created_count = 0
            for record_data in records:
                try:
                    oer_resource = OERResource.objects.create(
                        title=record_data.get('title', ''),
                        description=record_data.get('description', ''),
                        url=record_data.get('url', ''),
                        license=record_data.get('license', ''),
                        publisher=record_data.get('publisher', ''),
                        author=record_data.get('author', ''),
                        language=record_data.get('language', 'en'),
                        resource_type=record_data.get('resource_type', ''),
                        source=self.source
                    )
                    created_count += 1
                except Exception as e:
                    logger.warning(f"Failed to create OER resource: {str(e)}")
                    continue

            # Update harvest job
            harvest_job.status = 'completed'
            harvest_job.resources_found = len(records)
            harvest_job.resources_created = created_count
            harvest_job.completed_at = timezone.now()
            harvest_job.save()

            # Update source stats
            self.source.total_harvested += created_count
            self.source.last_harvest_at = timezone.now()
            self.source.save()

            return harvest_job

        except Exception as e:
            logger.error(f"Harvest failed: {str(e)}")
            harvest_job.status = 'failed'
            harvest_job.error_message = str(e)
            harvest_job.completed_at = timezone.now()
            harvest_job.save()
            raise

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
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return self._process_api_response(data)
            
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            raise ValidationError(f"API request failed: {str(e)}") from e

    def _process_api_response(self, data):
        """Process API response into OER resource data"""
        processed_records = []
        
        # Handle different API response structures
        records = data.get('results', data.get('items', data.get('data', [])))
        if not isinstance(records, list):
            records = [data]  # Single record response
        
        for record in records:
            try:
                # Map common API fields to OER resource model
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