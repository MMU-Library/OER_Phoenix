from django.urls import path
from django.contrib import admin
from django.views.generic import TemplateView
from .views import (
    ai_search, compare_view, csv_download, csv_upload, batch_ai_search, export_to_talis,
    export_resources, export_success, talis_csv_template, talis_preview,
    harvest_view, harvest_all_view, add_preset_view, test_connection_view
)

app_name = 'resources'

urlpatterns = [
    # Home page
    path('', TemplateView.as_view(template_name='admin/resources/home.html'), name='home'),
    
    # Search and comparison
    path('search/', ai_search, name='ai_search'),
    path('compare/', compare_view, name='compare_resources'),
    
    # CSV operations
    path('download-csv/', csv_download, name='csv_download'),
    path('upload/', csv_upload, name='csv_upload'),
    path('batch-ai-search/', batch_ai_search, name='batch_ai_search'),
    
    # Export operations
    path('export-to-talis/', export_to_talis, name='export_to_talis'),
    path('export/', export_resources, name='export_resources'),
    path('export-success/', export_success, name='export_success'),
    path('talis-csv-template/', talis_csv_template, name='talis_csv_template'),
    path('talis-preview/', talis_preview, name='talis_preview'),
    
    # OER Source management
    path('harvest/<int:source_id>/', harvest_view, name='harvest_oer_source'),
    path('harvest-all/', harvest_all_view, name='harvest_all_oer_sources'),
    path('add-preset/', add_preset_view, name='add_preset_oer_source'),
    path('test-connection/<int:source_id>/', test_connection_view, name='test_oer_source_connection'),
]