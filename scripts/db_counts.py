import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oer_rebirth.settings')
django.setup()
from resources.models import OERResource, HarvestJob
print('OERResource_count:%d' % OERResource.objects.count())
print('HarvestJob_count:%d' % HarvestJob.objects.count())
