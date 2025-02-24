from django.contrib import admin
from .models import Patient, LabRequest, TestPackage, TestComponent

admin.site.register(Patient)
admin.site.register(LabRequest)
admin.site.register(TestPackage)
admin.site.register(TestComponent)

