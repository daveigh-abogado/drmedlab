from django.contrib import admin
from .models import Patient, LabRequest, TestPackage, TestComponent, RequestLineItem, ResultValue, CollectionLog

admin.site.register(Patient)
admin.site.register(LabRequest)
admin.site.register(TestPackage)
admin.site.register(TestComponent)
admin.site.register(RequestLineItem)
admin.site.register(ResultValue)
admin.site.register(CollectionLog)

