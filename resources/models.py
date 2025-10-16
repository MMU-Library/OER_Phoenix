"""
OER Source Management Models
Dynamic configuration for OER API sources with admin interface
"""

from django.db import models
from django.core.validators import URLValidator
from django.utils import timezone
from pgvector.django import VectorField
import json

class OERResource(models.Model):
    """
    Educational resources fetched from various OER sources
    """
    # Basic Information
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    url = models.URLField(max_length=500)
    source = models.ForeignKey('OERSource', on_delete=models.CASCADE, related_name='resources')
    
    # Resource Details
    license = models.CharField(max_length=100, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    level = models.CharField(max_length=100, blank=True)
    publisher = models.CharField(max_length=200, blank=True)
    author = models.CharField(max_length=200, blank=True)
    language = models.CharField(max_length=50, blank=True, default='en')
    
    # Resource Type and Format
    resource_type = models.CharField(max_length=100, blank=True)
    format = models.CharField(max_length=100, blank=True)
    
    # AI/ML Fields
    content_embedding = VectorField(dimensions=384, null=True)  # For semantic search
    keywords = models.JSONField(default=list, blank=True)
    ai_generated_summary = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_verified = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "OER Resource"
        verbose_name_plural = "OER Resources"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title', 'source']),
            models.Index(fields=['resource_type', 'language']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.source.name})"


class OERSource(models.Model):
    """
    Configuration for external OER API sources
    Allows dynamic addition of new sources through admin interface
    """
    
    SOURCE_TYPE_CHOICES = [
        ('rest_api', 'REST API'),
        ('oai_pmh', 'OAI-PMH'),
        ('rss_feed', 'RSS Feed'),
        ('csv_url', 'CSV URL'),
        ('custom', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('testing', 'Testing'),
        ('error', 'Error'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200, unique=True, 
                           help_text="e.g., OAPEN, DOAB, OER Commons")
    description = models.TextField(blank=True, 
                                  help_text="Description of this OER source")
    website = models.URLField(blank=True, help_text="Main website URL")
    
    # API Configuration
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPE_CHOICES, 
                                  default='rest_api')
    api_endpoint = models.URLField(max_length=500, 
                                  help_text="Main API endpoint URL")
    api_key = models.CharField(max_length=500, blank=True, 
                              help_text="API key if required (stored securely)")
    
    # Request Configuration (JSON format)
    request_method = models.CharField(max_length=10, default='GET',
                                     choices=[('GET', 'GET'), ('POST', 'POST')])
    request_headers = models.JSONField(default=dict, blank=True,
                                      help_text='{"Authorization": "Bearer token", "Accept": "application/json"}')
    request_params = models.JSONField(default=dict, blank=True,
                                     help_text='{"format": "json", "per_page": 100}')
    
    # Response Mapping (JSON format)
    field_mappings = models.JSONField(
        default=dict,
        help_text='Map API fields to OER model fields: {"title": "data.attributes.title", "url": "data.links.self"}'
    )
    
    # Pagination Configuration
    supports_pagination = models.BooleanField(default=True)
    pagination_type = models.CharField(
        max_length=50,
        default='page_number',
        choices=[
            ('page_number', 'Page Number'),
            ('offset_limit', 'Offset/Limit'),
            ('cursor', 'Cursor'),
            ('link_header', 'Link Header'),
            ('none', 'No Pagination'),
        ]
    )
    pagination_config = models.JSONField(
        default=dict,
        blank=True,
        help_text='{"page_param": "page", "per_page_param": "per_page", "max_per_page": 100}'
    )
    
    # Data Extraction
    results_path = models.CharField(
        max_length=200,
        default='results',
        help_text="JSON path to results array: 'data', 'results', 'items', etc."
    )
    total_count_path = models.CharField(
        max_length=200,
        blank=True,
        help_text="JSON path to total count: 'meta.total', 'count', etc."
    )
    
    # Harvesting Configuration
    is_active = models.BooleanField(default=True, 
                                   help_text="Enable/disable harvesting from this source")
    harvest_schedule = models.CharField(
        max_length=50,
        default='daily',
        choices=[
            ('manual', 'Manual Only'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ]
    )
    max_resources_per_harvest = models.IntegerField(
        default=1000,
        help_text="Maximum resources to fetch per harvest (0 = unlimited)"
    )
    
    # Status & Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    last_harvest_at = models.DateTimeField(null=True, blank=True)
    last_harvest_count = models.IntegerField(default=0, 
                                            help_text="Resources harvested in last run")
    total_harvested = models.IntegerField(default=0, 
                                         help_text="Total resources harvested from this source")
    last_error = models.TextField(blank=True, help_text="Last error message if any")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "OER Source"
        verbose_name_plural = "OER Sources"
        ordering = ['-is_active', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def get_harvest_display_status(self):
        """Get human-readable harvest status"""
        if not self.is_active:
            return "Inactive"
        if self.last_harvest_at:
            days_ago = (timezone.now() - self.last_harvest_at).days
            return f"Last harvested {days_ago} days ago"
        return "Never harvested"


class HarvestJob(models.Model):
    """
    Track individual harvest jobs for monitoring and debugging
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial', 'Partially Completed'),
    ]
    
    source = models.ForeignKey(OERSource, on_delete=models.CASCADE, related_name='harvest_jobs')
    
    # Job Details
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Results
    resources_found = models.IntegerField(default=0)
    resources_created = models.IntegerField(default=0)
    resources_updated = models.IntegerField(default=0)
    resources_skipped = models.IntegerField(default=0)
    resources_failed = models.IntegerField(default=0)
    
    # Technical Details
    pages_processed = models.IntegerField(default=0)
    api_calls_made = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict, blank=True)
    
    # Logs
    log_messages = models.JSONField(default=list, blank=True,
                                   help_text="Array of log messages during harvest")
    
    # Metadata
    triggered_by = models.CharField(max_length=100, blank=True, 
                                   help_text="User or system that triggered harvest")
    
    class Meta:
        verbose_name = "Harvest Job"
        verbose_name_plural = "Harvest Jobs"
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['source', '-started_at']),
            models.Index(fields=['status', '-started_at']),
        ]
    
    def __str__(self):
        return f"{self.source.name} - {self.started_at.strftime('%Y-%m-%d %H:%M')} ({self.get_status_display()})"
    
    @property
    def duration(self):
        """Calculate job duration"""
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        return None
    
    def add_log(self, level, message):
        """Add a log message to the job"""
        if not isinstance(self.log_messages, list):
            self.log_messages = []
        
        self.log_messages.append({
            'timestamp': timezone.now().isoformat(),
            'level': level,
            'message': message
        })
        self.save(update_fields=['log_messages'])


class OERSourceFieldMapping(models.Model):
    """
    Detailed field mapping configuration for complex API responses
    Allows multiple mapping rules per source
    """
    
    source = models.ForeignKey(OERSource, on_delete=models.CASCADE, 
                             related_name='detailed_mappings')
    
    # Source Field
    source_field_path = models.CharField(max_length=300,
                                        help_text="JSON path in API response: 'data.attributes.title'")
    
    # Target Field
    target_field = models.CharField(max_length=100,
                                   help_text="OER model field name: 'title', 'description', etc.")
    
    # Transformation Rules
    is_required = models.BooleanField(default=False,
                                     help_text="Skip resource if this field is missing")
    default_value = models.CharField(max_length=500, blank=True,
                                    help_text="Default value if field is missing")
    transformation_rule = models.CharField(
        max_length=50,
        default='direct',
        choices=[
            ('direct', 'Direct Copy'),
            ('lowercase', 'Convert to Lowercase'),
            ('uppercase', 'Convert to Uppercase'),
            ('strip_html', 'Strip HTML Tags'),
            ('join_list', 'Join List with Comma'),
            ('first_item', 'Take First Item from List'),
            ('custom', 'Custom Transformation'),
        ]
    )
    custom_transformation = models.TextField(blank=True,
                                           help_text="Python code for custom transformation")
    
    # Priority
    priority = models.IntegerField(default=0,
                                  help_text="Processing order (higher = first)")
    
    class Meta:
        verbose_name = "Field Mapping"
        verbose_name_plural = "Field Mappings"
        ordering = ['-priority', 'target_field']
        unique_together = ['source', 'target_field']
    
    def __str__(self):
        return f"{self.source.name}: {self.source_field_path} → {self.target_field}"

