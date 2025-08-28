from django import forms
from .models import ModifiedMarkdownFile

class ModifiedMarkdownFileForm(forms.ModelForm):
    class Meta:
        model = ModifiedMarkdownFile
        fields = ["original_file", "modified_file"]
