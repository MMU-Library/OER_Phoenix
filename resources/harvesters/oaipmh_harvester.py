import requests
from xml.etree import ElementTree as ET
import logging
from django.core.exceptions import ValidationError
from django.utils import timezone
from resources.models import HarvestJob, OERResource

logger = logging.getLogger(__name__)

class OAIPMHHarvester:
    def __init__(self, source):
        self.source = source
        self.config = self._get_config()
        
    def _get_config(self):
        """Extract configuration from source model"""
        return {
            'base_url': self.source.oaipmh_url,
            'set_spec': self.source.oaipmh_set_spec,
            'metadata_prefix': 'oai_dc'  # Default to Dublin Core
        }

    def test_connection(self):
        """Test connection to OAI-PMH endpoint"""
        try:
            url = f"{self.config['base_url']}?verb=Identify"
            response = requests.get(url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"OAI-PMH connection test failed: {str(e)}")
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
            
            # Create or update OER resources
            created_count = 0
            updated_count = 0
            max_resources = getattr(self.source, 'max_resources_per_harvest', 0) or 0
            if max_resources > 0:
                records = records[:max_resources]

            for record_data in records:
                try:
                    resource, created = OERResource.objects.update_or_create(
                        url=record_data.get('url', ''),
                        defaults={
                            'title': record_data.get('title', ''),
                            'description': record_data.get('description', ''),
                            'license': record_data.get('license', ''),
                            'publisher': record_data.get('publisher', ''),
                            'author': record_data.get('author', ''),
                            'language': record_data.get('language', 'en'),
                            'resource_type': record_data.get('resource_type', ''),
                            'source': self.source
                        }
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                except Exception as e:
                    logger.warning(f"Failed to create/update OER resource: {str(e)}")
                    continue

            # Update harvest job
            harvest_job.status = 'completed'
            harvest_job.resources_found = len(records)
            harvest_job.resources_created = created_count
            harvest_job.resources_updated = updated_count
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

    def fetch_records(self):
        """Fetch records from OAI-PMH endpoint"""
        try:
            base_url = self.config["base_url"]
            metadata_prefix = self.config["metadata_prefix"]
            set_spec = self.config.get("set_spec")

            url = f"{base_url}?verb=ListRecords&metadataPrefix={metadata_prefix}"
            
            if set_spec:
                url += f"&set={set_spec}"

            logger.info(f"Fetching OAI-PMH records from: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            return ET.fromstring(response.content)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OAI-PMH request failed: {str(e)}")
            raise ValidationError(f"OAI-PMH request failed: {str(e)}") from e

    def process_record(self, record):
        """Process individual OAI-PMH record"""
        try:
            namespace = {
                'oai': 'http://www.openarchives.org/OAI/2.0/',
                'dc': 'http://purl.org/dc/elements/1.1/'
            }
            
            # Get metadata section
            metadata = record.find('.//oai:metadata', namespace)
            if not metadata:
                logger.warning("No metadata found in the record.")
                return None

            # Get Dublin Core data
            dc = metadata.find('.//dc:dc', namespace)
            if dc is None:
                return None

            def get_element_text(element, tag):
                elem = element.find(f'.//dc:{tag}', namespace)
                return elem.text if elem is not None else ''

            # Extract all available fields
            record_data = {
                'title': get_element_text(dc, 'title'),
                'description': get_element_text(dc, 'description'),
                'url': get_element_text(dc, 'identifier'),
                'license': get_element_text(dc, 'rights'),
                'publisher': get_element_text(dc, 'publisher'),
                'author': get_element_text(dc, 'creator'),
                'language': get_element_text(dc, 'language'),
                'resource_type': get_element_text(dc, 'type'),
                'subject': get_element_text(dc, 'subject'),
                'date': get_element_text(dc, 'date')
            }

            # Require at least title and URL
            if not record_data['title'] or not record_data['url']:
                return None
                
            return record_data
            
        except Exception as e:
            logger.warning(f"Failed to process OAI-PMH record: {str(e)}")
            return None

    def fetch_and_process_records(self):
        """Fetch and process all records"""
        try:
            root = self.fetch_records()
            processed_records = []
            
            # Process each record
            for record in root.findall('.//{http://www.openarchives.org/OAI/2.0/}record'):
                processed_record = self.process_record(record)
                if processed_record:
                    processed_records.append(processed_record)
                    
            logger.info(f"Processed {len(processed_records)} records from OAI-PMH")
            return processed_records
            
        except Exception as e:
            logger.error(f"Error processing OAI-PMH records: {str(e)}")
            raise