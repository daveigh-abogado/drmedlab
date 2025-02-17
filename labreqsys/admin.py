from django.contrib import admin
from .models import Patient, LabRequest

admin.site.register(Patient)
admin.site.register(LabRequest)
