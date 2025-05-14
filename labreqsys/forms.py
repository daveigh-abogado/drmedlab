from django import forms
from .models import LabTech
import re
from django.contrib.auth.models import User
from .models import UserProfile
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

class LabTechForm(forms.ModelForm):
    title = forms.ChoiceField(
        choices=[
            ('', 'Select title'),
            ('RMT', 'RMT (Registered Medical Technologist)'),
            ('MD', 'MD (Medical Doctor)'),
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    tech_role = forms.ChoiceField(
        choices=[
            ('', 'Select role'),
            ('Medical Technologist', 'Medical Technologist'),
            ('Pathologist', 'Pathologist'),
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = LabTech
        fields = ['first_name', 'last_name', 'title', 'tech_role', 'license_num']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name',
                'required': True,
                'pattern': '^[A-Za-z\\s]+$',
                'title': 'Use letters and spaces only'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name',
                'required': True,
                'pattern': '^[A-Za-z\\s]+$',
                'title': 'Use letters and spaces only'
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

class EditLabTechForm(LabTechForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove name fields as they shouldn't be editable
        if 'first_name' in self.fields:
            del self.fields['first_name']
        if 'last_name' in self.fields:
            del self.fields['last_name']
        # Make signature optional for editing
        self.fields['signature'].required = False

    class Meta(LabTechForm.Meta):
        fields = ['title', 'tech_role', 'license_num']  # Exclude name fields 

class UserRegistrationFormWithLabTech(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES)
    # Lab Tech extra fields (no signature)
    title = forms.ChoiceField(
        choices=[
            ('', 'Select title'),
            ('RMT', 'RMT (Registered Medical Technologist)'),
            ('MD', 'MD (Medical Doctor)'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tech_role = forms.ChoiceField(
        choices=[
            ('', 'Select role'),
            ('Medical Technologist', 'Medical Technologist'),
            ('Pathologist', 'Pathologist'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    license_num = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'email']

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        # If lab tech, require extra fields
        if role == 'lab_tech':
            for field in ['title', 'tech_role', 'license_num']:
                if not cleaned_data.get(field):
                    self.add_error(field, 'This field is required for Lab Tech.')
        return cleaned_data

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['role']

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput) 

class EditReceptionistProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class EditLabTechProfileForm(forms.ModelForm):
    title = forms.ChoiceField(
        choices=[
            ('', 'Select title'),
            ('RMT', 'RMT (Registered Medical Technologist)'),
            ('MD', 'MD (Medical Doctor)'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tech_role = forms.ChoiceField(
        choices=[
            ('', 'Select role'),
            ('Medical Technologist', 'Medical Technologist'),
            ('Pathologist', 'Pathologist'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    class Meta:
        model = LabTech
        fields = ['user', 'title', 'tech_role', 'license_num', 'signature_path']
        widgets = {
            'user': forms.HiddenInput(),
            'license_num': forms.TextInput(attrs={'class': 'form-control'}),
            'signature_path': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/png'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['signature_path'].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Only update signature_path if a new file is uploaded
        if self.cleaned_data.get('signature_path'):
            # The view will handle saving the file and setting the path
            pass
        else:
            # Do not overwrite signature_path if no new file is uploaded
            if self.instance.pk:
                orig = LabTech.objects.get(pk=self.instance.pk)
                instance.signature_path = orig.signature_path
        if commit:
            instance.save()
        return instance 