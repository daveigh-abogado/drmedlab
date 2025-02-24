from django.shortcuts import render, redirect, get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder
import json
from .models import Patient, LabRequest, CollectionLog, TestComponent, TemplateForm, TestPackage, TestPackageComponent
from datetime import date

def view_labreqs(request):
    labreqs = LabRequest.objects.all()
    return render(request, 'labreqsys/view_labreqs.html', {'labreqs':labreqs})

def base(request):
    return render(request, 'labreqsys/base.html')

def patientList(request):
    patients = Patient.objects.all()
    return render(request, 'labreqsys/patientList.html', {'patients':patients})

def add_labreq(request, pk):
    p = get_object_or_404(Patient, pk=pk)
    test_comps = TestComponent.objects.all()
    test_packages = TestPackage.objects.all()

    # Map package IDs to their component names
    package_data = {}
    for package in test_packages:
        components = TestPackageComponent.objects.filter(package=package).select_related('component')
        package_data[package.package_id] = [
            comp.component.test_name for comp in components
        ]

    return render(request, 'labreqsys/add_labreq.html', {
        'test_comps': test_comps,
        'test_packages': test_packages,
        'patient': p,
        'package_data': json.dumps(package_data, cls=DjangoJSONEncoder),  # Convert to JSON for JS use
    })

def view_patient(request, pk):
    p = get_object_or_404(Patient, pk=pk)
    full_name = p.last_name + ', ' + p.first_name

    if p.birthdate:
        today = date.today()
        age = today.year - p.birthdate.year - ((today.month, today.day) < (p.birthdate.month, p.birthdate.day))
    else:
        age = None

    #address = p.house_num + ' ' + p.street + ', ' + p.subdivision + ', ' + p.baranggay + ', ' + p.city + ', ' + p.province + ', ' + p.zip_code
    
    labreqs = LabRequest.objects.filter(patient_id=p.pk).values()
    return render(request, 'labreqsys/view_patient.html', {'patient': p, 'full_name':full_name, 'age': age, 'address':'testing', 'requests': labreqs, 'pickups': 'Collected', 'emails': 'Collected'}) # replace address here


def summarize_labreq(request, pk):
    p = get_object_or_404(Patient, pk=pk)
    temp_list_c = []
    temp_list_p = []
    if(request.method=="POST"):
        temp_list_c = request.POST.getlist('components')
        temp_list_p = request.POST.getlist('packages')
        hiddens = request.POST.getlist('selected_options')
    components = []
    packages = []
    for t in temp_list_c:
        temp = get_object_or_404(TestComponent, pk=t)
        components.append(temp)
    for t in temp_list_p:
        temp = get_object_or_404(TestPackage, pk=t)
        packages.append(temp)
    for t in hiddens:
        temp = get_object_or_404(TestPackage, pk=t)
        packages.append(temp)
    print("Received Packages:", temp_list_p)
    print("Received Components:", temp_list_c)
    return render(request, 'labreqsys/summarize_labreq.html', {'patient': p, 'components': components, 'packages': packages})