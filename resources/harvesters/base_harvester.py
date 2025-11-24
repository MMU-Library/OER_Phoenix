from abc import ABC, abstractmethod
import logging
from django.utils import timezone
import resources.harvesters.utils as utils

logger = logging.getLogger(__name__)


class BaseHarvester(ABC):
    """Shared harvester base class providing common harvest flow and helpers.

    Subclasses must implement `fetch_and_process_records()` and may override
    `test_connection()` if needed.
    """

    def __init__(self, source):
        self.source = source

    def create_harvest_job(self):
        # import models lazily so this module can be imported without Django setup
        from resources.models import HarvestJob
        return HarvestJob.objects.create(
            source=self.source,
            status='running',
            started_at=timezone.now()
        )

    def record_samples(self, harvest_job, records, n=5):
        try:
            samples = []
            for r in records[:n]:
                samples.append({'title': r.get('title', ''), 'url': r.get('url', '')})
            if samples:
                logs = harvest_job.log_messages or []
                logs.append({'sample_records': samples})
                harvest_job.log_messages = logs
                harvest_job.save()
        except Exception:
            logger.exception('Failed to write sample records to HarvestJob.log_messages')

    def upsert_resource(self, record_data):
        # Ensure URL key exists for matching; empty URL leads to skipped upsert outside
        try:
            # import model lazily
            from resources.models import OERResource
            # Sanitize/truncate fields to fit model max_length constraints
            def _t(v, maxlen=None):
                if v is None:
                    return ''
                s = str(v)
                if maxlen and len(s) > maxlen:
                    return s[:maxlen]
                return s

            defaults = {
                'title': _t(record_data.get('title', ''), maxlen=500),
                'description': record_data.get('description', ''),
                'license': _t(record_data.get('license', ''), maxlen=100),
                'publisher': _t(record_data.get('publisher', ''), maxlen=200),
                'author': _t(record_data.get('author', ''), maxlen=200),
                'language': _t(record_data.get('language', 'en'), maxlen=50),
                'resource_type': _t(record_data.get('resource_type', ''), maxlen=100),
                'source': self.source
            }

            resource, created = OERResource.objects.update_or_create(
                url=_t(record_data.get('url', ''), maxlen=500),
                defaults=defaults
            )
            return resource, created
        except Exception:
            logger.exception('Failed to upsert resource')
            raise

    def request(self, method, url, headers=None, params=None, timeout=15, max_attempts=3):
        return utils.request_with_retry(method, url, headers=headers, params=params, timeout=timeout, max_attempts=max_attempts)

    def harvest(self):
        """Generic harvest flow used by most harvesters.

        Calls `fetch_and_process_records()` implemented by subclass, upserts
        records and updates a `HarvestJob` with counts and sample records.
        """
        harvest_job = self.create_harvest_job()
        try:
            records = self.fetch_and_process_records()

            created_count = 0
            updated_count = 0
            max_resources = getattr(self.source, 'max_resources_per_harvest', 0) or 0
            if max_resources > 0:
                records = records[:max_resources]

            for record_data in records:
                try:
                    resource, created = self.upsert_resource(record_data)
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                except Exception:
                    harvest_job.resources_failed += 1
                    continue

            harvest_job.status = 'completed'
            harvest_job.resources_found = len(records)
            harvest_job.resources_created = created_count
            harvest_job.resources_updated = updated_count
            harvest_job.completed_at = timezone.now()
            harvest_job.save()

            # update source stats
            try:
                self.source.total_harvested += created_count
                self.source.last_harvest_at = timezone.now()
                self.source.save()
            except Exception:
                logger.exception('Failed to update source stats')

            # store samples for debugging
            try:
                self.record_samples(harvest_job, records, n=5)
            except Exception:
                pass

            return harvest_job

        except Exception as e:
            logger.exception('Harvest failed')
            harvest_job.status = 'failed'
            harvest_job.error_message = str(e)
            harvest_job.completed_at = timezone.now()
            harvest_job.save()
            raise

    @abstractmethod
    def fetch_and_process_records(self):
        """Return list of record dicts with at least `title` and `url` keys."""
        raise NotImplementedError()
