"""
Enhanced Django Admin for OER Source Management
Includes "Harvest OER" button and management interface
"""

from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.http import JsonResponse
from resources.models import OERSource, HarvestJob, OERSourceFieldMapping
from resources.services.oer_harvester import OERHarvester, PresetHarvesterConfigs
from .views import harvest_view, harvest_all_view, add_preset_view, test_connection_view

class OERSourceFieldMappingInline(admin.TabularInline):
    """Inline admin for field mappings"""
    model = OERSourceFieldMapping
    extra = 1

@admin.register(OERSource)
class OERSourceAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'status_badge',
        'harvest_stats',
        'last_harvest_display',
        'harvest_action_buttons'
    ]
    
    list_filter = ['is_active', 'status']
    search_fields = ['name', 'description']
    readonly_fields = [
        'status', 
        'last_harvest_at', 
        'last_harvest_count', 
        'total_harvested', 
        'last_error'
    ]
    
    inlines = [OERSourceFieldMappingInline]
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            'active': 'green',
            'inactive': 'gray',
            'testing': 'orange',
            'error': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def harvest_stats(self, obj):
        """Display harvest statistics"""
        return format_html(
            '<strong>{}</strong> total<br><small>Last: {}</small>',
            obj.total_harvested,
            obj.last_harvest_count
        )
    harvest_stats.short_description = 'Harvested'
    
    def last_harvest_display(self, obj):
        """Display last harvest time"""
        if obj.last_harvest_at:
            return obj.last_harvest_at.strftime('%Y-%m-%d %H:%M')
        return mark_safe('<em>Never</em>')
    last_harvest_display.short_description = 'Last Harvest'
    
    def harvest_action_buttons(self, obj):
        """Display harvest action buttons"""
        if not obj.is_active:
            return mark_safe('<em>Inactive</em>')
        
        harvest_url = reverse('admin:harvest_oer_source', args=[obj.pk])
        view_jobs_url = reverse('admin:resources_harvestjob_changelist') + f'?source__id__exact={obj.pk}'
        test_url = reverse('admin:test_oer_source_connection', args=[obj.pk])
        
        return format_html(
            '<a class="button" href="{}" style="background-color: #417690; '
            'color: white; padding: 5px 10px; text-decoration: none; '
            'border-radius: 3px; margin-right: 5px;">🌾 Harvest Now</a>'
            '<a class="button" href="{}" style="background-color: #28a745; '
            'color: white; padding: 5px 10px; text-decoration: none; '
            'border-radius: 3px; margin-right: 5px;">🔍 Test Connection</a>'
            '<a class="button" href="{}" style="padding: 5px 10px;">View Jobs</a>',
            harvest_url,
            test_url,
            view_jobs_url
        )
    harvest_action_buttons.short_description = 'Actions'
    harvest_action_buttons.allow_tags = True
    
    def get_urls(self):
        """Add custom URLs for harvest actions"""
        urls = super().get_urls()
        custom_urls = [
            path('harvest/<int:source_id>/', 
                 self.admin_site.admin_view(harvest_view), 
                 name='harvest_oer_source'),
            path('harvest-all/', 
                 self.admin_site.admin_view(harvest_all_view), 
                 name='harvest_all_oer_sources'),
            path('add-preset/', 
                 self.admin_site.admin_view(add_preset_view), 
                 name='add_preset_oer_source'),
            path('test-connection/<int:source_id>/', 
                 self.admin_site.admin_view(test_connection_view),
                 name='test_oer_source_connection'),
        ]
        return custom_urls + urls

@admin.register(HarvestJob)
class HarvestJobAdmin(admin.ModelAdmin):
    """Admin for viewing harvest job history"""
    
    list_display = [
        'id',
        'source',
        'started_at',
        'status_badge',
        'duration_display',
        'results_summary'
    ]
    
    list_filter = ['status', 'source', 'started_at']
    search_fields = ['source__name', 'error_message']
    readonly_fields = [
        'source', 
        'started_at', 
        'completed_at', 
        'status',
        'resources_found', 
        'resources_created', 
        'resources_updated',
        'resources_skipped', 
        'resources_failed', 
        'pages_processed',
        'api_calls_made', 
        'error_message', 
        'error_details',
        'log_messages', 
        'triggered_by'
    ]
    
    fieldsets = (
        ('Job Information', {
            'fields': ('source', 'started_at', 'completed_at', 'status', 'triggered_by')
        }),
        ('Results', {
            'fields': ('resources_found', 'resources_created', 'resources_updated',
                      'resources_skipped', 'resources_failed')
        }),
        ('Technical Details', {
            'fields': ('pages_processed', 'api_calls_made', 'error_message', 'error_details')
        }),
        ('Logs', {
            'fields': ('log_messages',),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            'pending': 'gray',
            'running': 'blue',
            'completed': 'green',
            'failed': 'red',
            'partial': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def duration_display(self, obj):
        """Display job duration"""
        if obj.duration:
            total_seconds = int(obj.duration.total_seconds())
            minutes, seconds = divmod(total_seconds, 60)
            return f"{minutes}m {seconds}s"
        return mark_safe('<em>In progress...</em>')
    duration_display.short_description = 'Duration'
    
    def results_summary(self, obj):
        """Display results summary"""
        return format_html(
            '<strong>+{}</strong> created, <strong>{}</strong> updated, <em>{}</em> skipped',
            obj.resources_created,
            obj.resources_updated,
            obj.resources_skipped
        )
    results_summary.short_description = 'Results'
    
    def has_add_permission(self, request):
        """Prevent manual creation of harvest jobs"""
        return False