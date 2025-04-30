from django import forms
from .models import LabTech
import re

class LabTechForm(forms.ModelForm):
    class Meta:
        model = LabTech
        fields = ['first_name', 'last_name', 'title', 'tech_role', 'license_num']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name',
                'required': True
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter title (e.g., Medical Technologist)',
                'required': True
            }),
            'tech_role': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter role (e.g., Clinical Chemistry)',
                'required': True
            }),
            'license_num': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter license number',
                'required': True
            }),
        }
        
    signature = forms.ImageField(
        required=True,
        help_text='Upload signature image (PNG format)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/png'
        })
    )

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name.replace(' ', '').isalpha():
            raise forms.ValidationError('First name should only contain letters.')
        return first_name.strip()

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name.replace(' ', '').isalpha():
            raise forms.ValidationError('Last name should only contain letters.')
        return last_name.strip()

    def clean_license_num(self):
        license_num = self.cleaned_data.get('license_num')
        if not re.match(r'^[0-9A-Za-z-]+$', license_num):
            raise forms.ValidationError('License number should only contain letters, numbers, and hyphens.')
        return license_num.strip()

    def clean_signature(self):
        signature = self.cleaned_data.get('signature')
        if signature:
            if not signature.name.lower().endswith('.png'):
                raise forms.ValidationError('Only PNG files are allowed for signatures.')
            if signature.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError('Signature file size should be less than 5MB.')
        return signature 