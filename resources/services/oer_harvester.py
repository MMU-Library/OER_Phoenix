"""
OER Harvester Service
Dynamic harvesting from configured OER sources with flexible API support
"""

import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from django.utils import timezone
from django.db import transaction
import logging
import time

logger = logging.getLogger(__name__)


class OERHarvester:
    """
    Main harvester class for pulling OER resources from external APIs
    Supports multiple API types and configurations
    """
    
    def __init__(self, source):
        """
        Initialize harvester with an OERSource configuration
        
        Args:
            source: OERSource model instance
        """
        self.source = source
        self.session = requests.Session()
        self.session.headers.update(source.request_headers or {})
        self.harvest_job = None
        
        # Rate limiting
        self.rate_limit_delay = 1.0  # seconds between requests
        self.last_request_time = 0
    
    def harvest(self, max_pages: int = None, dry_run: bool = False) -> Dict:
        """
        Main harvest method
        
        Args:
            max_pages: Maximum pages to fetch (None = all available)
            dry_run: If True, don't save to database
            
        Returns:
            Dictionary with harvest statistics
        """
        from resources.models import HarvestJob
        
        # Create harvest job record
        self.harvest_job = HarvestJob.objects.create(
            source=self.source,
            status='running',
            triggered_by='admin'
        )
        
        try:
            self.harvest_job.add_log('info', f'Starting harvest from {self.source.name}')
            
            # Harvest based on source type
            if self.source.source_type == 'rest_api':
                results = self._harvest_rest_api(max_pages, dry_run)
            elif self.source.source_type == 'oai_pmh':
                results = self._harvest_oai_pmh(max_pages, dry_run)
            elif self.source.source_type == 'rss_feed':
                results = self._harvest_rss(dry_run)
            elif self.source.source_type == 'csv_url':
                results = self._harvest_csv(dry_run)
            else:
                raise ValueError(f"Unsupported source type: {self.source.source_type}")
            
            # Update job status
            self.harvest_job.status = 'completed'
            self.harvest_job.completed_at = timezone.now()
            self.harvest_job.resources_found = results['found']
            self.harvest_job.resources_created = results['created']
            self.harvest_job.resources_updated = results['updated']
            self.harvest_job.resources_skipped = results['skipped']
            self.harvest_job.save()
            
            # Update source
            self.source.last_harvest_at = timezone.now()
            self.source.last_harvest_count = results['created']
            self.source.total_harvested += results['created']
            self.source.status = 'active'
            self.source.last_error = ''
            self.source.save()
            
            self.harvest_job.add_log('info', f'Harvest completed successfully')
            
            return results
            
        except Exception as e:
            logger.error(f"Harvest failed for {self.source.name}: {str(e)}")
            
            # Update job with error
            self.harvest_job.status = 'failed'
            self.harvest_job.completed_at = timezone.now()
            self.harvest_job.error_message = str(e)
            self.harvest_job.save()
            
            # Update source
            self.source.status = 'error'
            self.source.last_error = str(e)
            self.source.save()
            
            raise
    
    def _harvest_rest_api(self, max_pages: int, dry_run: bool) -> Dict:
        """Harvest from REST API with pagination"""
        results = {'found': 0, 'created': 0, 'updated': 0, 'skipped': 0}
        page = 1
        
        while True:
            # Rate limiting
            self._rate_limit()
            
            # Build request
            url = self.source.api_endpoint
            params = dict(self.source.request_params or {})
            
            # Add pagination parameters
            if self.source.supports_pagination:
                params.update(self._get_pagination_params(page))
            
            # Make request
            try:
                self.harvest_job.add_log('info', f'Fetching page {page} from {url}')
                response = self._make_request(url, params)
                self.harvest_job.api_calls_made += 1
                self.harvest_job.pages_processed += 1
                self.harvest_job.save()
                
                # Extract resources
                resources_data = self._extract_resources(response)
                
                if not resources_data:
                    self.harvest_job.add_log('info', f'No more resources found on page {page}')
                    break
                
                results['found'] += len(resources_data)
                
                # Process each resource
                for resource_data in resources_data:
                    try:
                        status = self._process_resource(resource_data, dry_run)
                        results[status] += 1
                    except Exception as e:
                        logger.warning(f"Failed to process resource: {str(e)}")
                        results['skipped'] += 1
                
                # Check if we should continue
                if not self.source.supports_pagination:
                    break
                
                if max_pages and page >= max_pages:
                    self.harvest_job.add_log('info', f'Reached max pages limit: {max_pages}')
                    break
                
                if not self._has_next_page(response):
                    self.harvest_job.add_log('info', 'No more pages available')
                    break
                
                page += 1
                
                # Check max resources limit
                if (self.source.max_resources_per_harvest > 0 and 
                    results['found'] >= self.source.max_resources_per_harvest):
                    self.harvest_job.add_log('info', 'Reached max resources limit')
                    break
                
            except Exception as e:
                logger.error(f"Error on page {page}: {str(e)}")
                self.harvest_job.add_log('error', f'Error on page {page}: {str(e)}')
                raise
        
        return results
    
    def _harvest_oai_pmh(self, max_pages: int, dry_run: bool) -> Dict:
        """Harvest from OAI-PMH endpoint"""
        results = {'found': 0, 'created': 0, 'updated': 0, 'skipped': 0}
        
        # OAI-PMH specific implementation
        # TODO: Implement OAI-PMH harvesting
        self.harvest_job.add_log('warning', 'OAI-PMH harvesting not yet implemented')
        
        return results
    
    def _harvest_rss(self, dry_run: bool) -> Dict:
        """Harvest from RSS feed"""
        results = {'found': 0, 'created': 0, 'updated': 0, 'skipped': 0}
        
        # RSS specific implementation
        # TODO: Implement RSS harvesting
        self.harvest_job.add_log('warning', 'RSS harvesting not yet implemented')
        
        return results
    
    def _harvest_csv(self, dry_run: bool) -> Dict:
        """Harvest from CSV URL"""
        results = {'found': 0, 'created': 0, 'updated': 0, 'skipped': 0}
        
        # CSV specific implementation
        # TODO: Implement CSV harvesting
        self.harvest_job.add_log('warning', 'CSV harvesting not yet implemented')
        
        return results
    
    def _make_request(self, url: str, params: Dict) -> Dict:
        """Make HTTP request with error handling"""
        try:
            if self.source.request_method == 'POST':
                response = self.session.post(
                    url,
                    json=params,
                    timeout=30
                )
            else:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=30
                )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise
    
    def _extract_resources(self, response_data: Dict) -> List[Dict]:
        """Extract resource array from API response"""
        results_path = self.source.results_path
        
        # Navigate JSON path
        data = response_data
        for key in results_path.split('.'):
            if isinstance(data, dict):
                data = data.get(key, [])
            else:
                break
        
        if isinstance(data, list):
            return data
        
        return []
    
    def _process_resource(self, resource_data: Dict, dry_run: bool) -> str:
        """
        Process a single resource from API response
        
        Returns:
            'created', 'updated', or 'skipped'
        """
        from resources.models import OERResource
        
        # Map fields
        mapped_data = self._map_fields(resource_data)
        
        # Validate required fields
        if not mapped_data.get('title') or not mapped_data.get('url'):
            logger.warning(f"Missing required fields: {mapped_data}")
            return 'skipped'
        
        if dry_run:
            logger.info(f"DRY RUN: Would create/update resource: {mapped_data.get('title')}")
            return 'created'
        
        # Check if resource exists
        url = mapped_data['url']
        existing = OERResource.objects.filter(url=url).first()
        
        if existing:
            # Update existing resource
            for key, value in mapped_data.items():
                setattr(existing, key, value)
            existing.source = self.source.name
            existing.save()
            return 'updated'
        else:
            # Create new resource
            OERResource.objects.create(
                source=self.source.name,
                **mapped_data
            )
            return 'created'
    
    def _map_fields(self, resource_data: Dict) -> Dict:
        """Map API fields to OER model fields"""
        mapped = {}
        
        field_mappings = self.source.field_mappings or {}
        
        for target_field, source_path in field_mappings.items():
            value = self._get_nested_value(resource_data, source_path)
            
            if value is not None:
                # Apply transformations
                value = self._transform_value(value, target_field)
                mapped[target_field] = value
        
        return mapped
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Extract value from nested JSON path"""
        if not path:
            return None
        
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit():
                try:
                    value = value[int(key)]
                except IndexError:
                    return None
            else:
                return None
            
            if value is None:
                return None
        
        return value
    
    def _transform_value(self, value: Any, target_field: str) -> Any:
        """Apply transformations to extracted value"""
        # Join lists
        if isinstance(value, list):
            value = ', '.join(str(v) for v in value)
        
        # Convert to string and clean
        if isinstance(value, str):
            value = value.strip()
        
        # Field-specific transformations
        if target_field in ['description', 'learning_objectives']:
            # Strip HTML tags if present
            import re
            value = re.sub(r'<[^>]+>', '', str(value))
        
        return value
    
    def _get_pagination_params(self, page: int) -> Dict:
        """Get pagination parameters for current page"""
        config = self.source.pagination_config or {}
        
        if self.source.pagination_type == 'page_number':
            return {
                config.get('page_param', 'page'): page,
                config.get('per_page_param', 'per_page'): config.get('max_per_page', 100)
            }
        elif self.source.pagination_type == 'offset_limit':
            per_page = config.get('max_per_page', 100)
            return {
                config.get('offset_param', 'offset'): (page - 1) * per_page,
                config.get('limit_param', 'limit'): per_page
            }
        
        return {}
    
    def _has_next_page(self, response_data: Dict) -> bool:
        """Check if there are more pages to fetch"""
        config = self.source.pagination_config or {}
        
        # Check for next link
        next_link_path = config.get('next_link_path', 'links.next')
        next_link = self._get_nested_value(response_data, next_link_path)
        if next_link:
            return True
        
        # Check if current page has maximum items
        resources = self._extract_resources(response_data)
        max_per_page = config.get('max_per_page', 100)
        
        return len(resources) >= max_per_page
    
    def _rate_limit(self):
        """Implement rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()


class PresetHarvesterConfigs:
    """
    Preset configurations for common OER sources
    """
    
    @staticmethod
    def get_oapen_config():
        """OAPEN Library configuration"""
        return {
            'name': 'OAPEN Library',
            'description': 'Open Access Publishing in European Networks',
            'website': 'https://oapen.org',
            'source_type': 'rest_api',
            'api_endpoint': 'https://library.oapen.org/rest/search',
            'request_params': {
                'query': '*:*',
                'expand': 'metadata'
            },
            'field_mappings': {
                'title': 'metadata.dc.title',
                'description': 'metadata.dc.description.abstract',
                'url': 'handle',
                'publisher': 'metadata.dc.publisher',
                'license': 'metadata.dc.rights',
                'subject_area': 'metadata.dc.subject',
            },
            'results_path': 'expand',
            'supports_pagination': True,
            'pagination_type': 'offset_limit',
            'pagination_config': {
                'offset_param': 'start',
                'limit_param': 'limit',
                'max_per_page': 100
            }
        }
    
    @staticmethod
    def get_doab_config():
        """DOAB (Directory of Open Access Books) configuration"""
        return {
            'name': 'DOAB',
            'description': 'Directory of Open Access Books',
            'website': 'https://www.doabooks.org',
            'source_type': 'oai_pmh',
            'api_endpoint': 'https://www.doabooks.org/oai',
            'request_params': {
                'verb': 'ListRecords',
                'metadataPrefix': 'oai_dc'
            },
            'field_mappings': {
                'title': 'metadata.dc:title',
                'description': 'metadata.dc:description',
                'url': 'metadata.dc:identifier',
                'publisher': 'metadata.dc:publisher',
                'license': 'metadata.dc:rights',
            },
        }
    
    @staticmethod
    def get_openstax_config():
        """OpenStax configuration"""
        return {
            'name': 'OpenStax',
            'description': 'Free textbooks for college courses',
            'website': 'https://openstax.org',
            'source_type': 'rest_api',
            'api_endpoint': 'https://openstax.org/api/v2/pages/',
            'request_params': {
                'type': 'books.Book',
                'fields': '*'
            },
            'field_mappings': {
                'title': 'title',
                'description': 'description',
                'url': 'book_student_resources.resource_unlocked_url',
                'subject_area': 'subject',
                'publisher': 'authors',
                'license': 'license_name',
            },
            'results_path': 'items',
            'supports_pagination': True,
            'pagination_type': 'page_number',
        }
