import csv
import io
import logging
import requests
import time
from django.core.exceptions import ValidationError
from django.utils import timezone
from resources.models import HarvestJob, OERResource

logger = logging.getLogger(__name__)

class CSVHarvester:
    def __init__(self, source):
        self.source = source
        self.config = self._get_config()

    def _get_config(self):
        return {
            'csv_url': self.source.csv_url,
        }

    def test_connection(self):
        try:
            url = self.config['csv_url']
            response = requests.head(url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"CSV connection test failed: {str(e)}")
            return False

    def harvest(self):
        harvest_job = HarvestJob.objects.create(
            source=self.source,
            status='running',
            started_at=timezone.now()
        )
        try:
            records = self.fetch_and_process_records()
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
                    logger.warning(f"Failed to create/update OER resource from CSV: {str(e)}")
                    continue
            harvest_job.status = 'completed'
            harvest_job.resources_found = len(records)
            harvest_job.resources_created = created_count
            harvest_job.resources_updated = updated_count
            harvest_job.completed_at = timezone.now()
            harvest_job.save()
            self.source.total_harvested += created_count
            self.source.last_harvest_at = timezone.now()
            self.source.save()
            return harvest_job
        except Exception as e:
            logger.error(f"CSV harvest failed: {str(e)}")
            harvest_job.status = 'failed'
            harvest_job.error_message = str(e)
            harvest_job.completed_at = timezone.now()
            harvest_job.save()
            raise

    def fetch_and_process_records(self):
        try:
            url = self.config['csv_url']
            # Retry on transient server errors
            attempts = 0
            response = None
            while attempts < 3:
                attempts += 1
                response = requests.get(url, timeout=60)
                if response.status_code >= 500:
                    logger.warning(f"CSV fetch attempt {attempts} returned {response.status_code}, retrying...")
                    time.sleep(2 * attempts)
                    continue
                break
            if response is None:
                raise ValidationError("Failed to fetch CSV: no response")
            response.raise_for_status()
            content = response.content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            processed_records = []
            # Prepare candidate column names (case-insensitive) for common fields
            def first_present(row, candidates, default=''):
                # Use case-insensitive matching for keys
                lower_map = {k.lower(): k for k in row.keys()}
                for cand in candidates:
                    if cand.lower() in lower_map:
                        return row.get(lower_map[cand.lower()], '')
                return default

            title_candidates = ['dc.title', 'title', 'Title', 'dc.title.alternative', 'dc.title_alternative']
            url_candidates = ['BITSTREAM_Download_URL', 'dc.identifier.uri', 'url', 'URL', 'link', 'identifier', 'dc.identifier']
            desc_candidates = ['dc.description.abstract', 'description', 'dc.description', 'abstract']
            license_candidates = ['BITSTREAM_License', 'dc.rights', 'license', 'rights']
            publisher_candidates = ['publisher', 'dc.publisher', 'oapen.relation.isPublishedBy_publisher.name']
            author_candidates = ['dc.contributor.author', 'author', 'dc.creator', 'dc.contributor']
            language_candidates = ['dc.language', 'language', 'lang']
            type_candidates = ['type', 'dc.type', 'oapen.relation.isPartOfBook']

            for row in reader:
                # Map CSV columns to OERResource fields using flexible candidate lists
                record_data = {
                    'title': first_present(row, title_candidates, '').strip(),
                    'description': first_present(row, desc_candidates, '').strip(),
                    'url': first_present(row, url_candidates, '').strip(),
                    'license': first_present(row, license_candidates, '').strip(),
                    'publisher': first_present(row, publisher_candidates, '').strip(),
                    'author': first_present(row, author_candidates, '').strip(),
                    'language': first_present(row, language_candidates, 'en').strip(),
                    'resource_type': first_present(row, type_candidates, '').strip(),
                }

                # Some URLs may be relative or empty; skip invalid rows
                if record_data['title'] and record_data['url']:
                    processed_records.append(record_data)
            logger.info(f"Processed {len(processed_records)} records from CSV")
            return processed_records
        except Exception as e:
            logger.error(f"Error processing CSV records: {str(e)}")
            raise
