from django.shortcuts import render, redirect, get_object_or_404
from .models import OERResource, OERSource
from .forms import BulkCSVUploadForm
from .services.oer_harvester import OERHarvester, PresetHarvesterConfigs
import csv
from django.contrib import messages
from django.http import HttpResponse
import io

def ai_search(request):
    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        if not query:
            return render(request, 'resources/search.html', {
                'results': [],
                'query': query,
                'ai_search': True
            })
        # Implement your AI search logic here
        results = []
        
        return render(request, 'resources/search.html', {
            'results': results,
            'query': query,
            'ai_search': True
        })
    return render(request, 'resources/search.html', {
        'results': [],
        'query': '',
        'ai_search': True
    })

def compare_view(request):
    """
    View for comparing multiple OER resources
    """
    resource_ids = request.session.get('comparison_resources', [])
    resources = OERResource.objects.filter(id__in=resource_ids) if resource_ids else []
    
    return render(request, 'resources/compare.html', {
        'resources': resources
    })

def csv_upload(request):
    if request.method == 'POST':
        form = BulkCSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            reader = csv.DictReader(io.TextIOWrapper(csv_file, encoding='utf-8', errors='replace'))
            reader.fieldnames = [fn.strip().replace('\ufeff', '') for fn in reader.fieldnames if fn and fn.strip()]
            required_columns = ['title', 'source', 'description', 'license', 'url']
            if not all(col in reader.fieldnames for col in required_columns):
                messages.error(request, "CSV is missing required columns")
                return redirect('resources:csv_upload')

            created = []
            skipped = []
            for row in reader:
                title = row.get('title', '').strip()
                url = row.get('url', '').strip()
                if not title or not url:
                    skipped.append(row)
                    continue
                if OERResource.objects.filter(title=title, url=url).exists():
                    skipped.append(row)
                    continue
                resource = OERResource.objects.create(
                    title=title,
                    source_id=row.get('source', ''),
                    description=row.get('description', ''),
                    license=row.get('license', ''),
                    url=url,
                )
                created.append(resource)

            messages.success(request, f"CSV uploaded! {len(created)} resources created, {len(skipped)} skipped.")
            request.session['uploaded_resource_ids'] = [r.id for r in created]
            return redirect('resources:batch_ai_search')
    else:
        form = BulkCSVUploadForm()

    return render(request, "resources/csv_upload.html", {"form": form})

# Export and Download Views
def csv_download(request):
    """Download resources as CSV"""
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

def batch_ai_search(request):
    """Process uploaded resources with AI"""
    resource_ids = request.session.get('uploaded_resource_ids', [])
    resources = OERResource.objects.filter(id__in=resource_ids)
    
    # TODO: Implement AI processing logic
    
    return render(request, 'resources/search.html', {
        'results': resources,
        'batch_processed': True
    })

def export_to_talis(request):
    """Export resources to Talis format"""
    if request.method == 'POST':
        selected_ids = request.POST.getlist('resource_ids')
        resources = OERResource.objects.filter(id__in=selected_ids)
        request.session['export_resources'] = list(selected_ids)
        return redirect('resources:talis_preview')
    
    resources = OERResource.objects.all()
    return render(request, 'resources/export.html', {'resources': resources})

def export_resources(request):
    """General resource export view"""
    resources = OERResource.objects.all()
    return render(request, 'resources/export.html', {'resources': resources})

def export_success(request):
    """Show export success page"""
    return render(request, 'resources/export_success.html')

def talis_csv_template(request):
    """Download Talis CSV template"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="talis_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Title', 'URL', 'Description', 'Type', 'Author'])
    return response

def talis_preview(request):
    """Preview Talis export"""
    resource_ids = request.session.get('export_resources', [])
    resources = OERResource.objects.filter(id__in=resource_ids)
    return render(request, 'resources/talis_preview.html', {'resources': resources})

def harvest_view(request, source_id):
    """Handle harvest request for a specific OER source"""
    source = get_object_or_404(OERSource, pk=source_id)
    try:
        harvester = OERHarvester(source)
        job = harvester.start_harvest_job()
        messages.success(request, f"Started harvesting {source.name}")
        return redirect('admin:resources_harvestjob_changelist')
    except Exception as e:
        messages.error(request, f"Error starting harvest: {str(e)}")
        return redirect('admin:resources_oersource_changelist')

def harvest_all_view(request):
    """Handle harvest request for all active OER sources"""
    sources = OERSource.objects.filter(is_active=True)
    try:
        for source in sources:
            harvester = OERHarvester(source)
            harvester.start_harvest_job()
        messages.success(request, f"Started harvesting {sources.count()} sources")
    except Exception as e:
        messages.error(request, f"Error starting harvest: {str(e)}")
    return redirect('admin:resources_oersource_changelist')

def add_preset_view(request):
    """Add a preset OER source configuration"""
    if request.method == 'POST':
        preset_name = request.POST.get('preset_name')
        if preset_name in PresetHarvesterConfigs:
            config = PresetHarvesterConfigs[preset_name]
            source = OERSource.objects.create(**config)
            messages.success(request, f"Added preset source: {source.name}")
        else:
            messages.error(request, "Invalid preset name")
    return redirect('admin:resources_oersource_changelist')

def test_connection_view(request, source_id):
    """Test connection to an OER source"""
    source = get_object_or_404(OERSource, pk=source_id)
    try:
        harvester = OERHarvester(source)
        success = harvester.test_connection()
        if success:
            messages.success(request, f"Successfully connected to {source.name}")
        else:
            messages.warning(request, f"Could not connect to {source.name}")
    except Exception as e:
        messages.error(request, f"Connection error: {str(e)}")
    return redirect('admin:resources_oersource_changelist')