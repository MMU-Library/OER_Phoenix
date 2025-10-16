from django import forms
from .models import OERSource

class BulkCSVUploadForm(forms.Form):
    csv_file = forms.FileField(label="Select CSV file")

class ExportForm(forms.Form):
    title = forms.CharField(max_length=255, required=True)
    description = forms.CharField(widget=forms.Textarea, required=False)
    source_ids = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=[]
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['source_ids'].choices = [
            (s.id, s.name) for s in OERSource.objects.all()
        ]
