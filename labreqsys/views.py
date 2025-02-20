from django.shortcuts import render, redirect, get_object_or_404
from .models import Patient, LabRequest, CollectionLog, TestComponent, TemplateForm
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
    return render(request, 'labreqsys/add_labreq.html', {'test_comps': test_comps, 'patient': p})

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
    if(request.method=="POST"):
        temp_list = request.POST.getlist('components')
    components = []
    for t in temp_list:
        temp = get_object_or_404(TestComponent, pk=t)
        components.append(temp)
    return render(request, 'labreqsys/summarize_labreq.html', {'patient': p, 'components': components})