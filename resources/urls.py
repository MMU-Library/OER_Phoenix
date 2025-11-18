from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    # Home page - use the resources home template
    path('', views.home, name='home'),
    
    # Search and comparison - use resources templates
    path('search/', views.ai_search, name='ai_search'),
    path('compare/', views.compare_view, name='compare_resources'),

    # CSV operations - mixed templates
    path('download-csv/', views.csv_download, name='csv_download'),
    path('upload-csv/', views.csv_upload, name='csv_upload'),  # Admin template
    path('bulk-csv-upload/', views.bulk_csv_upload, name='bulk_csv_upload'),  # Admin template

    # Export operations - mixed templates
    path('export/', views.export_resources, name='export_resources'),  # Resources template
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/json/', views.export_json, name='export_json'),
    path('export/talis/', views.export_to_talis, name='export_to_talis'),
    path('export/talis/template/', views.talis_csv_template, name='talis_csv_template'),
    path('export/talis/preview/', views.talis_preview, name='talis_preview'),
    path('export/success/', views.export_success, name='export_success'),
    path('export-data/', views.export_data, name='export_data'),  # Admin template
    
    # OER Source management (admin functions) - Admin templates
    path('harvest/<int:source_id>/', views.harvest_view, name='harvest_oer_source'),
    path('test-connection/<int:source_id>/', views.test_connection_view, name='test_oer_source_connection'),
    path('apply-preset/', views.apply_preset_view, name='apply_preset'),
    
    # Dynamic form handling - Admin templates
    path('create-source/', views.create_source, name='create_source'),
    path('load-configuration-form/', views.load_configuration_form, name='load_configuration_form'),
]