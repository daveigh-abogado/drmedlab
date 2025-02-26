from django.shortcuts import render, redirect, get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder
import json
from .models import Patient, LabRequest, CollectionLog, TestComponent, TemplateForm, TestPackage, TestPackageComponent
from datetime import date, datetime
from decimal import Decimal

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

def add_labreq_details(request, pk):
    p = get_object_or_404(Patient, pk=pk)
    if(request.method=="POST"):
        request.session.flush()
        selected_packages = request.POST.getlist('selected_packages')
        selected_components = request.POST.getlist('selected_components')
    request.session['selected_components'] = selected_components
    request.session['selected_packages'] = selected_packages
    return render(request, 'labreqsys/add_labreq_details.html', {'patient': p})

def summarize_labreq(request, pk):
    p = get_object_or_404(Patient, pk=pk)
    sc = request.session.get('selected_components', [])
    sp = request.session.get('selected_packages', [])
    
    total = 0
    
    components = []
    packages = []
    
    for t in sc:
        temp = get_object_or_404(TestComponent, pk=t)
        total = temp.component_price + total    
        components.append(temp)
        
    for t in sp:
        temp = get_object_or_404(TestPackage, pk=t)
        total = temp.package_price + total
        packages.append(temp)
        
    if p.pwd_id_num is not None or p.senior_id_num is not None: 
        discount = round(total * Decimal(0.2), 2)
        total = total - round(discount)
        
        # 022521 [Mads]: Not sure if VAT-exemption already applies to their pricing so I'll just add this jic.
        """
        discount_vat = price * Decimal(0.12)
        payment_vat = price - discount_vat
        discount = payment_vat * Decimal(0.2)
        payment = price - round(discount + discount_vat)
        """
            
    current_date = datetime.today().strftime('%Y-%m-%d')
    if(request.method=="POST"):
        physician = request.POST.get('physician')
        mode = request.POST.getlist('mode_of_release')

    if 'Pick-Up' in mode and 'Email' in mode:
        mode_of_release = 'Both'
    else:
        if 'Pick-Up' in mode:
            mode_of_release = 'Pick-up'
        else:
            mode_of_release = 'Email'
            
    LabRequest.objects.create(patient = p, date_requested = current_date, physician = physician, mode_of_release = mode_of_release, overall_status = "Not Started")
    return render(request, 'labreqsys/summarize_labreq.html', {
        'patient': p,
        'components': components,
        'packages': packages,
        'total' : total,
        'date': current_date,
        'physician': physician,
        'mode_of_release': mode_of_release,
        'discount' : discount
    })

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
def view_individual_lab_request(request, request_id):
    lab_request = get_object_or_404(LabRequest, pk=request_id)
    request_details = lab_request.get_request_details()
    return render(request, 'labreqsys/lab_request_details.html', {'request_details': request_details})
