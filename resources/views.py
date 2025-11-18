# views.py -
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from .harvesters.preset_configs import PRESET_CONFIGS
import csv
import io
import json
import logging

from .models import OERResource, OERSource, HarvestJob
from .forms import (
    CSVUploadForm, ExportForm, APIHarvesterForm, OAIPMHHarvesterForm, 
    CSVHarvesterForm, TalisExportForm, HarvesterTypeForm
)
from .harvesters.api_harvester import APIHarvester
from .harvesters.oaipmh_harvester import OAIPMHHarvester
from .harvesters.preset_configs import PresetAPIConfigs, PresetOAIPMHConfigs

logger = logging.getLogger(__name__)

def staff_required(view_func):
    """Decorator for views that require staff membership"""
    return user_passes_test(lambda u: u.is_staff)(view_func)

# Template path constants for consistency
TEMPLATE_ADMIN_HOME = 'admin/resources/home.html'
TEMPLATE_RESOURCES_HOME = 'resources/home.html'
TEMPLATE_SEARCH = 'resources/search.html'
TEMPLATE_COMPARE = 'resources/compare.html'
TEMPLATE_CSV_UPLOAD = 'admin/resources/csv_upload.html'
TEMPLATE_EXPORT = 'resources/export.html'
TEMPLATE_EXPORT_SUCCESS = 'resources/export_success.html'
TEMPLATE_TALIS_PREVIEW = 'resources/talis_preview.html'
TEMPLATE_BULK_CSV_UPLOAD = 'admin/resources/csv_upload.html'
TEMPLATE_EXPORT_DATA = 'admin/resources/export.html'
TEMPLATE_CREATE_SOURCE = 'admin/resources/create_source.html'
TEMPLATE_ADD_HARVESTER = 'admin/resources/add_harvester.html'
TEMPLATE_OERSOURCE_HARVEST = 'admin/resources/oersource_harvest.html'

# Search Views
def ai_search(request):
    """AI-powered search view"""
    try:
        if request.method == 'POST':
            query = request.POST.get('query', '').strip()
            if not query:
                return render(request, TEMPLATE_SEARCH, {
                    'results': [],
                    'query': query,
                    'ai_search': True
                })
            
            # Implement AI search logic here
            results = OERResource.objects.filter(
                title__icontains=query
            ) | OERResource.objects.filter(
                description__icontains=query
            )
            
            return render(request, TEMPLATE_SEARCH, {
                'results': results,
                'query': query,
                'ai_search': True
            })
        return render(request, TEMPLATE_SEARCH, {
            'results': [],
            'query': '',
            'ai_search': True
        })
    except Exception as e:
        logger.error(f"Error in ai_search: {str(e)}")
        messages.error(request, "An error occurred during the search.")
        return redirect('resources:ai_search')

def compare_view(request):
    """View for comparing multiple OER resources"""
    try:
        resource_ids = request.session.get('comparison_resources', [])
        resources = OERResource.objects.filter(id__in=resource_ids) if resource_ids else []
        
        return render(request, TEMPLATE_COMPARE, {
            'resources': resources
        })
    except Exception as e:
        logger.error(f"Error in compare_view: {str(e)}")
        messages.error(request, "An error occurred while loading the comparison view.")
        return redirect('resources:home')

# Home View - Use the existing template
def home(request):
    """Home dashboard view"""
    try:
        context = {
            'total_resources': OERResource.objects.count(),
            'total_sources': OERSource.objects.count(),
            'recent_jobs': HarvestJob.objects.order_by('-started_at')[:5]
        }
        # Use the existing home template from templates/resources/
        return render(request, TEMPLATE_RESOURCES_HOME, context)
    except Exception as e:
        logger.error(f"Error in home view: {str(e)}")
        # Fallback with empty context
        return render(request, TEMPLATE_RESOURCES_HOME, {
            'total_resources': 0,
            'total_sources': 0,
            'recent_jobs': []
        })

# CSV Operations
def csv_upload(request):
    """Handle CSV file uploads - Admin template"""
    try:
        if request.method == 'POST':
            form = CSVUploadForm(request.POST, request.FILES)
            
            if form.is_valid():
                csv_file = request.FILES['csv_file']
                
                # Validate file type
                if not csv_file.name.lower().endswith(('.csv', '.tsv')):
                    messages.error(request, "Please upload a CSV or TSV file.")
                    return redirect('resources:csv_upload')
                
                delimiter = ',' if csv_file.name.lower().endswith('.csv') else '\t'
                reader = csv.DictReader(
                    io.TextIOWrapper(csv_file.file, encoding='utf-8'),
                    delimiter=delimiter
                )
                
                # Process CSV data here
                processed_count = 0
                for row in reader:
                    # Add your CSV processing logic here
                    processed_count += 1
                
                messages.success(request, f"Successfully processed {processed_count} records from '{csv_file.name}'.")
                return redirect('resources:csv_upload')
            else:
                logger.error(f"Invalid form submission in csv_upload: {form.errors}")
                messages.error(request, "Error validating the form.")
                return redirect('resources:csv_upload')
        else:
            form = CSVUploadForm()
            
        return render(request, TEMPLATE_CSV_UPLOAD, {'form': form})
    except Exception as e:
        logger.error(f"Error in csv_upload: {str(e)}")
        messages.error(request, "An error occurred during file upload.")
        return redirect('resources:csv_upload')

def csv_download(request):
    """Download resources as CSV"""
    try:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="oer_resources.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Title', 'Description', 'URL', 'License', 'Source'])
        
        for resource in OERResource.objects.all():
            writer.writerow([
                resource.title,
                resource.description,
                resource.url,
                resource.license,
                resource.source.name if resource.source else ''
            ])
        
        return response
    except Exception as e:
        logger.error(f"Error in csv_download: {str(e)}")
        messages.error(request, "An error occurred while generating the CSV file.")
        return redirect('resources:home')

# Export Views
def export_to_talis(request):
    """Export resources to Talis format"""
    try:
        if request.method == 'POST':
            form = TalisExportForm(request.POST)
            if form.is_valid():
                selected_resources = form.cleaned_data['resource_ids']
                
                # Validate selection
                if not selected_resources.exists():
                    messages.error(request, "No resources were selected for export.")
                    return redirect('resources:export_to_talis')
                
                request.session['export_resources'] = list(selected_resources.values_list('id', flat=True))
                request.session['talis_title'] = form.cleaned_data['title']
                request.session['talis_description'] = form.cleaned_data.get('description', '')
                
                return redirect('resources:talis_preview')
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            form = TalisExportForm()
        
        return render(request, 'resources/export.html', {'form': form})
    except Exception as e:
        logger.error(f"Error in export_to_talis: {str(e)}")
        messages.error(request, "An error occurred during the export process.")
        return redirect('resources:home')

def talis_csv_template(request):
    """Download Talis CSV template"""
    try:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="talis_template.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Title', 'URL', 'Description', 'Type', 'Author'])
        return response
    except Exception as e:
        logger.error(f"Error in talis_csv_template: {str(e)}")
        messages.error(request, "An error occurred while generating the template.")
        return redirect('resources:home')

def talis_preview(request):
    """Preview Talis export"""
    try:
        resource_ids = request.session.get('export_resources', [])
        resources = OERResource.objects.filter(id__in=resource_ids) if resource_ids else []
        
        return render(request, TEMPLATE_TALIS_PREVIEW, {
            'resources': resources,
            'talis_title': request.session.get('talis_title', ''),
            'talis_description': request.session.get('talis_description', '')
        })
    except Exception as e:
        logger.error(f"Error in talis_preview: {str(e)}")
        messages.error(request, "An error occurred while loading the preview.")
        return redirect('resources:home')

# Harvesting Views
@staff_required
def harvest_view(request, source_id):
    """Handle harvest request for a specific OER source"""
    try:
        source = get_object_or_404(OERSource, pk=source_id)
        
        if request.method == 'POST':
            # Determine the harvester class based on source configuration
            if source.source_type == 'API':
                harvester = APIHarvester(source)
            elif source.source_type == 'OAIPMH':
                harvester = OAIPMHHarvester(source)
            else:
                messages.error(request, f"Unsupported harvester type: {source.source_type}")
                return redirect('admin:resources_oersource_changelist')

            # Start harvest job
            job = harvester.harvest()
            messages.success(request, f"Started harvesting from {source.name} (Job: {job.id})")
            return redirect('admin:resources_harvestjob_changelist')
        
        # GET request - show harvest confirmation form
        return render(request, TEMPLATE_OERSOURCE_HARVEST, {'source': source})
        
    except Exception as e:
        logger.error(f"Error in harvest_view: {str(e)}")
        messages.error(request, f"Error starting harvest: {str(e)}")
        return redirect('admin:resources_oersource_changelist')

@staff_required
def test_connection_view(request, source_id):
    """Handle test connection request for an OER source"""
    try:
        source = get_object_or_404(OERSource, pk=source_id)
        
        # Determine the harvester class based on source configuration
        if source.source_type == 'API':
            harvester = APIHarvester(source)
        elif source.source_type == 'OAIPMH':
            harvester = OAIPMHHarvester(source)
        else:
            messages.error(request, f"Unsupported harvester type: {source.source_type}")
            return redirect('admin:resources_oersource_changelist')

        success = harvester.test_connection()
        
        if success:
            messages.success(request, f"Successfully connected to {source.name}")
        else:
            messages.warning(request, f"Could not connect to {source.name}")
            
    except Exception as e:
        logger.error(f"Error in test_connection_view: {str(e)}")
        messages.error(request, f"Connection error: {str(e)}")
    
    return redirect('admin:resources_oersource_changelist')

# Source Management Views
@staff_required
@require_http_methods(['GET', 'POST'])
def create_source(request):
    """Create a new OER source - Admin template"""
    try:
        if request.method == 'POST':
            source_type = request.POST.get('source_type')
            form_class = get_form_class(source_type)
            
            if not form_class:
                messages.error(request, "Invalid source type.")
                return redirect('admin:resources_oersource_changelist')
                
            form = form_class(request.POST)
            if form.is_valid():
                source = form.save()
                messages.success(request, f"Successfully created {source_type} source: {source.name}")
                return redirect('admin:resources_oersource_changelist')
            else:
                logger.error(f"Invalid form submission in create_source: {form.errors}")
                messages.error(request, "Error validating the form.")
        else:
            # GET request - show source type selection
            return render(request, 'admin/resources/create_source.html')
        
        # If form is invalid, re-render with errors
        context = {
            'form': form,
            'source_type': source_type
        }
        return render(request, TEMPLATE_CREATE_SOURCE, context)
    except Exception as e:
        logger.error(f"Error in create_source: {str(e)}")
        messages.error(request, "An error occurred while creating the source.")
        return redirect('admin:resources_oersource_changelist')

def get_form_class(source_type):
    """Helper function to determine form class based on source type"""
    form_classes = {
        'API': APIHarvesterForm,
        'OAIPMH': OAIPMHHarvesterForm,
        'CSV': CSVHarvesterForm
    }
    return form_classes.get(source_type)

@staff_required
@require_http_methods(['GET'])
def load_configuration_form(request):
    """Load configuration form based on source type"""
    try:
        source_type = request.GET.get('source_type')
        form_class = get_form_class(source_type)
        
        if not form_class:
            return JsonResponse({'error': 'Invalid source type'}, status=400)
            
        form = form_class()
        
        # Render form to HTML string
        form_html = render(request, 'admin/resources/partials/source_config_form.html', {'form': form}).content.decode()
        
        return JsonResponse({'form_html': form_html})
    except Exception as e:
        logger.error(f"Error in load_configuration_form: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@staff_required
def add_preset_view(request):
    """Add preset harvester view - Admin template"""
    harvester_type = request.GET.get('type', 'API')
    form_class = get_form_class(harvester_type)
    
    if not form_class:
        messages.error(request, "Invalid harvester type.")
        return redirect('admin:resources_oersource_changelist')
        
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            source = form.save()
            messages.success(request, f"Successfully created {harvester_type} source: {source.name}")
            return redirect('admin:resources_oersource_changelist')
    else:
        form = form_class()
    
    return render(request, TEMPLATE_ADD_HARVESTER, {
        'form': form,
        'harvester_type': harvester_type
    })

@staff_required
def apply_preset_view(request):
    """Apply a preset configuration to create a new source"""
    if request.method == 'POST':
        try:
            source_type = request.POST.get('source_type')
            preset_key = request.POST.get('preset_key')
            
            if not source_type or not preset_key:
                messages.error(request, "Missing source type or preset key.")
                return redirect('admin:resources_oersource_add')
            
            # Get the preset configuration
            preset = PRESET_CONFIGS.get(source_type, {}).get(preset_key)
            
            if not preset:
                messages.error(request, f"Preset not found: {preset_key}")
                return redirect('admin:resources_oersource_add')
            
            # Use dicts directly for JSONFields
            request_params = preset.get('request_params', {})
            request_headers = preset.get('request_headers', {})

            # Create the source with preset values (JSONFields accept dicts)
            source = OERSource.objects.create(
                name=preset['name'],
                description=preset['description'],
                source_type=source_type,
                api_endpoint=preset.get('api_endpoint', ''),
                oaipmh_url=preset.get('oaipmh_url', ''),
                csv_url=preset.get('csv_url', ''),
                request_params=request_params,
                request_headers=request_headers,
                oaipmh_set_spec=preset.get('oaipmh_set_spec', ''),
                harvest_schedule=preset.get('harvest_schedule', 'manual'),
                max_resources_per_harvest=preset.get('max_resources_per_harvest', 1000),
                is_active=True
            )
            
            messages.success(request, f"Successfully created {source.name} from preset.")
            return redirect('admin:resources_oersource_change', object_id=source.id)
            
        except Exception as e:
            logger.error(f"Error applying preset: {str(e)}")
            messages.error(request, f"Error applying preset: {str(e)}")
            return redirect('admin:resources_oersource_add')
    
    return redirect('admin:resources_oersource_add')

# Export Functions
def export_resources(request):
    """Export resources view for regular users (non-admin)"""
    if request.method == 'POST':
        form = ExportForm(request.POST)
        if form.is_valid():
            export_type = form.cleaned_data['export_type']
            
            if export_type == 'CSV':
                return export_csv(request)
            elif export_type == 'JSON':
                return export_json(request)
    else:
        form = ExportForm()
    
    # Add statistics to context
    total_resources = OERResource.objects.count()
    active_resources = OERResource.objects.filter(is_active=True).count()
    
    return render(request, TEMPLATE_EXPORT, {
        'form': form,
        'total_resources': total_resources,
        'active_resources': active_resources,
    })

def export_csv(request):
    """Export resources as CSV for regular users"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="oer_resources.csv"'
    
    writer = csv.writer(response)
    # Write CSV header
    writer.writerow([
        'Title', 'Description', 'URL', 'License', 'Subject', 
        'Level', 'Publisher', 'Author', 'Language', 'Resource Type',
        'Source', 'Created Date'
    ])
    
    # Write data rows
    for resource in OERResource.objects.all():
        writer.writerow([
            resource.title,
            resource.description,
            resource.url,
            resource.license,
            resource.subject,
            resource.level,
            resource.publisher,
            resource.author,
            resource.language,
            resource.resource_type,
            resource.source.name if resource.source else '',
            resource.created_at.strftime('%Y-%m-%d') if resource.created_at else ''
        ])
    
    return response

def export_json(request):
    """Export resources as JSON for regular users"""
    resources = OERResource.objects.all()
    data = serializers.serialize('json', resources)
    
    response = JsonResponse({'resources': data}, safe=False)
    response['Content-Disposition'] = 'attachment; filename="oer_resources.json"'
    return response

# Bulk Operations
@staff_required
def bulk_csv_upload(request):
    """Handle bulk CSV file uploads - Admin template"""
    try:
        if request.method == 'POST':
            form = CSVUploadForm(request.POST, request.FILES)
            
            if form.is_valid():
                csv_file = request.FILES['csv_file']
                
                # Validate file type
                if not csv_file.name.lower().endswith(('.csv', '.tsv')):
                    messages.error(request, "Please upload a CSV or TSV file.")
                    return redirect('resources:bulk_csv_upload')
                
                delimiter = ',' if csv_file.name.lower().endswith('.csv') else '\t'
                reader = csv.DictReader(
                    io.TextIOWrapper(csv_file.file, encoding='utf-8'),
                    delimiter=delimiter
                )
                
                # Process the file
                processed_count = 0
                for row in reader:
                    # Add bulk processing logic here
                    processed_count += 1
                
                messages.success(request, f"Bulk upload completed. Processed {processed_count} records.")
                return redirect('resources:bulk_csv_upload')
            else:
                logger.error(f"Invalid form submission in bulk_csv_upload: {form.errors}")
                messages.error(request, "Error validating the form.")
                return redirect('resources:bulk_csv_upload')
        else:
            form = CSVUploadForm()
            
        return render(request, TEMPLATE_BULK_CSV_UPLOAD, {'form': form})
    except Exception as e:
        logger.error(f"Error in bulk_csv_upload: {str(e)}")
        messages.error(request, "An error occurred during bulk file upload.")
        return redirect('resources:home')

@staff_required
def export_data(request):
    """General data export view for admin"""
    try:
        if request.method == 'POST':
            form = ExportForm(request.POST)
            
            if form.is_valid():
                export_type = form.cleaned_data['export_type']
                
                if export_type == 'CSV':
                    return export_csv(request)
                elif export_type == 'JSON':
                    return export_json(request)
            else:
                logger.error(f"Invalid form submission in export_data: {form.errors}")
                messages.error(request, "Error validating the form.")
        else:
            form = ExportForm()
        
        return render(request, TEMPLATE_EXPORT_DATA, {'form': form})
    except Exception as e:
        logger.error(f"Error in export_data: {str(e)}")
        messages.error(request, "An error occurred during data export.")
        return redirect('admin:index')

# Success Views
def export_success(request):
    """Show export success page"""
    try:
        return render(request, TEMPLATE_EXPORT_SUCCESS)
    except Exception as e:
        logger.error(f"Error in export_success: {str(e)}")
        messages.error(request, "An error occurred while displaying the success page.")
        return redirect('resources:home')