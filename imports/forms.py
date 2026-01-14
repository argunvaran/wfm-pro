from django import forms
from .models import ImportJob

class ImportForm(forms.ModelForm):
    class Meta:
        model = ImportJob
        fields = ['import_type', 'file']
