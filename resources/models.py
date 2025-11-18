# models.py
"""
OER Source Management Models
Dynamic configuration for OER API sources with admin interface
"""

from django.db import models
from django.core.validators import URLValidator
from django.utils import timezone
from pgvector.django import VectorField
import json

class OERSource(models.Model):
    """
    Configuration for external OER API sources
    Allows dynamic addition of new sources through admin interface
    """
    # Harvester Type - FIXED CHOICES
    SOURCE_TYPES = [
        ('API', 'API Harvester'),
        ('OAIPMH', 'OAI-PMH Harvester'),
        ('CSV', 'CSV Harvester'),  # ADDED CSV
    ]
    
    source_type = models.CharField(
        max_length=20,  # CHANGED from 50 to 20 to match choices
        choices=SOURCE_TYPES,
        default='API',
        help_text="Select the type of harvester to use for this source"
    )
    
    # Basic Information
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    
    # API Configuration
    api_endpoint = models.URLField(
        blank=True,
        null=True,
        help_text="API endpoint URL (e.g., https://example.com/api/v1/resources)"
    )
    api_key = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="API key if required (stored securely)"
    )
    request_headers = models.JSONField(
        default=dict,
        blank=True,
        help_text='{"Authorization": "Bearer token", "Accept": "application/json"}'
    )
    request_params = models.JSONField(
        default=dict,
        blank=True,
        help_text='{"format": "json", "per_page": 100}'
    )
    
    # OAI-PMH Configuration
    oaipmh_url = models.URLField(
        blank=True,
        null=True,
        help_text="OAI-PMH URL (e.g., https://example.com/oai)"
    )
    oaipmh_set_spec = models.CharField(
        max_length=200,
        blank=True,
        help_text="Set specification for the OAI-PMH harvest"
    )
    
    # CSV Configuration
    csv_url = models.URLField(
        blank=True,
        null=True,
        help_text="CSV file URL for CSV harvesting"
    )
    
    # Field Mappings
    field_mappings = models.ManyToManyField(
        'OERSourceFieldMapping',
        related_name='sources',
        blank=True,
        help_text="Map API fields to OER model fields"
    )
    
    # Harvesting Configuration
    is_active = models.BooleanField(default=True)
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
    STATUS_CHOICES = [  # ADDED consistent status choices
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('testing', 'Testing'),
        ('error', 'Error'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    last_harvest_at = models.DateTimeField(null=True, blank=True)
    total_harvested = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "OER Source"
        verbose_name_plural = "OER Sources"
        ordering = ['-is_active', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

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
    content_embedding = VectorField(dimensions=384, null=True, blank=True)  # Added blank=True
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

class OERSourceFieldMapping(models.Model):
    """
    Detailed field mapping configuration for complex API responses
    Allows multiple mapping rules per source
    """
    
    # Source Field Configuration
    source_field_path = models.CharField(
        max_length=300,
        help_text="JSON path in API response (e.g., 'data.attributes.title')"
    )
    
    # Target Field Configuration
    target_model_fields = models.JSONField(
        default=dict,
        help_text='{"OERResource": {"title": "data.title", "description": "data.description"}}'
    )
    
    # Transformation Rules
    is_required = models.BooleanField(default=False)
    default_value = models.CharField(max_length=500, blank=True)
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
    
    # Custom Transformation
    custom_transformation = models.TextField(
        blank=True,
        help_text="Python code for custom transformation (e.g., lambda x: x.upper())"
    )
    
    class Meta:
        verbose_name = "Field Mapping"
        verbose_name_plural = "Field Mappings"
        ordering = ['-is_required', 'target_model_fields']
    
    def __str__(self):
        return f"{self.source_field_path} → {list(self.target_model_fields.keys())[0]}"

class HarvestJob(models.Model):
    """
    Represents a harvesting job for an OER source.
    Tracks the status and results of each harvesting attempt.
    """
    source = models.ForeignKey('OERSource', on_delete=models.CASCADE, related_name='harvest_jobs')
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),  # CHANGED from 'queued' to 'pending'
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('partial', 'Partial'),  # ADDED partial status
        ],
        default='pending'
    )
    
    # Time tracking
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Resource counts
    resources_found = models.IntegerField(default=0)
    resources_created = models.IntegerField(default=0)
    resources_updated = models.IntegerField(default=0)
    resources_skipped = models.IntegerField(default=0)
    resources_failed = models.IntegerField(default=0)
    
    # Technical details
    pages_processed = models.IntegerField(default=0)
    api_calls_made = models.IntegerField(default=0)
    
    # Error handling
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(default=dict, blank=True)
    log_messages = models.JSONField(default=list, blank=True)
    
    # Metadata
    triggered_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Harvest Job"
        verbose_name_plural = "Harvest Jobs"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Harvest job for {self.source.name} ({self.get_status_display()})"
    
    @property
    def duration(self):
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def total_resources_harvested(self):
        return self.resources_created + self.resources_updated