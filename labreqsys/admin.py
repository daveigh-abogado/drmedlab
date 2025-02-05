from django.contrib import admin
from .models import Patients, LabRequest

admin.site.register(Patients)
admin.site.register(LabRequest)
