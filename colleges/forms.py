from django import forms
from .models import College

class CollegeForm(forms.ModelForm):
    class Meta:
        model = College
        fields = [
            'college_name',
            'college_code',
            'email',
            'max_pass',
            'status'
        ]
        widgets = {
            'college_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. PSG College of Technology'}),
            'college_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. PSG01'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'e.g. contact@psg.edu'}),
            'max_pass': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '10'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
