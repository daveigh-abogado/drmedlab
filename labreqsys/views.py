from django.shortcuts import render
from .models import Patient, LabRequest

def view_labreqs(request):
    labreqs = LabRequest.objects.all()
    return render(request, 'labreqsys/view_labreqs.html', {'labreqs':labreqs})
def base(request):
    return render(request, 'labreqsys/base.html')

def patientList(request):
    patients = Patient.objects.all()
    return render(request, 'labreqsys/patientList.html', {'patients':patients})
