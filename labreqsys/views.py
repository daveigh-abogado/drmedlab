from django.shortcuts import render, redirect, get_object_or_404
from .models import Patient, LabRequest, CollectionLog, TestComponent, TemplateForm, TestPackage
from datetime import date
from decimal import *

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
    return render(request, 'labreqsys/add_labreq.html', {'test_comps': test_comps, 'test_packages': test_packages, 'patient': p})

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
        temp_list_c = request.POST.getlist('components')
        temp_list_p = request.POST.getlist('packages')

    # [REMOVE] 022225 Mads: TEMP ONLY ! For checking if it works only.
    temp_list_c = [1, 2, 3, 4]
    temp_list_p = [1, 2]
    
    total = 0
    
    components = []
    packages = []
    
    for t in temp_list_c:
        temp = get_object_or_404(TestComponent, pk=t)
        to_pay = discount(p, temp.component_price)
        total = to_pay + total    
        components.append(temp)
        
    for t in temp_list_p:
        temp = get_object_or_404(TestPackage, pk=t)
        to_pay = discount(p, temp.package_price)
        total = to_pay + total
        packages.append(temp)
    
    return render(request, 'labreqsys/summarize_labreq.html', {'patient': p, 'components': components, 'packages': packages, 'total' : total })

def discount(patient, price):
    if patient.pwd_id_num is None or patient.senior_id_num is None: 
        return price
        
    else:
        discount = price * Decimal(0.2)
        payment = price - round(discount)
        
        # 022521 [Mads]: Not sure if VAT-exemption already applies to their pricing so I'll just add this jic.
        """
        discount_vat = price * Decimal(0.12)
        payment_vat = price - discount_vat
        discount = payment_vat * Decimal(0.2)
        payment = price - round(discount + discount_vat)
        """
        
        return payment