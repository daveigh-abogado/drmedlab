from django.shortcuts import render, redirect, get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder
import json
from .models import Patient, LabRequest, CollectionLog, TestComponent, TemplateForm, TestPackage, TestPackageComponent, RequestLineItem, TemplateSection, TemplateField, LabTech, ResultValue, ResultReview
from datetime import date, datetime
from decimal import Decimal

# Utility functions
def discount(patient, price):
    """
    Calculate the discount for a patient based on PWD or senior citizen status.
    """
    if patient.pwd_id_num is None or patient.senior_id_num is None: 
        return price
    else:
        discount = price * Decimal(0.2)
        payment = price - round(discount)
        return payment

# View functions
def base(request):
    """
    Render the base template.
    """
    return render(request, 'labreqsys/base.html')

def view_labreqs(request):
    """
    Display a list of all lab requests.
    """
    labreqs = LabRequest.objects.all()
    return render(request, 'labreqsys/view_labreqs.html', {'labreqs': labreqs})

def patientList(request):
    """
    Display a list of all patients.
    """
    patients = Patient.objects.all()
    return render(request, 'labreqsys/patientList.html', {'patients': patients})

def labRequests(request):
    """
    Display a list of all lab requests.
    """
    labreqs = LabRequest.objects.select_related('patient').all()
    
    return render(request, 'labreqsys/labRequests.html', {'labreqs': labreqs})

def view_patient(request, pk):
    """
    Display detailed information about a specific patient.
    """
    p = get_object_or_404(Patient, pk=pk)
    full_name = f"{p.last_name}, {p.first_name}"

    if p.birthdate:
        today = date.today()
        age = today.year - p.birthdate.year - ((today.month, today.day) < (p.birthdate.month, p.birthdate.day))
    else:
        age = None

    labreqs = LabRequest.objects.filter(patient_id=p.pk).values()
    return render(request, 'labreqsys/view_patient.html', {
        'patient': p,
        'full_name': full_name,
        'age': age,
        'address': 'testing',  # Replace with actual address
        'requests': labreqs,
        'pickups': 'Collected',  # Replace with actual pickup status
        'emails': 'Collected'  # Replace with actual email status
    })

def add_labreq(request, pk):
    """
    Display a form to add a new lab request for a specific patient.
    """
    p = get_object_or_404(Patient, pk=pk)
    test_comps = TestComponent.objects.all()
    test_packages = TestPackage.objects.all()

    # Map package IDs to their component names
    package_data = {}
    for package in test_packages:
        components = TestPackageComponent.objects.filter(package=package).select_related('component')
        package_data[package.package_id] = [comp.component.test_name for comp in components]

    return render(request, 'labreqsys/add_labreq.html', {
        'test_comps': test_comps,
        'test_packages': test_packages,
        'patient': p,
        'package_data': json.dumps(package_data, cls=DjangoJSONEncoder),  # Convert to JSON for JS use
    })

def add_labreq_details(request, pk):
    """
    Handle the selection of components and packages for a new lab request.
    """
    p = get_object_or_404(Patient, pk=pk)
    if request.method == "POST":
        request.session.flush()
        selected_packages = request.POST.getlist('selected_packages')
        selected_components = request.POST.getlist('selected_components')
        request.session['selected_components'] = selected_components
        request.session['selected_packages'] = selected_packages
    return render(request, 'labreqsys/add_labreq_details.html', {'patient': p})

def summarize_labreq(request, pk):
    """
    Summarize the selected components and packages for a new lab request and calculate the total cost.
    """
    p = get_object_or_404(Patient, pk=pk)
    sc = request.session.get('selected_components', [])
    sp = request.session.get('selected_packages', [])
    
    total = 0
    components = []
    packages = []
    
    for t in sc:
        temp = get_object_or_404(TestComponent, pk=t)
        total += temp.component_price
        components.append(temp)
        
    for t in sp:
        temp = get_object_or_404(TestPackage, pk=t)
        total += temp.package_price
        packages.append(temp)
        
    discount = 0
    if p.pwd_id_num is not None or p.senior_id_num is not None: 
        discount = round(total * Decimal(0.2), 2)
        total -= discount
    
    current_date = datetime.today().strftime('%Y-%m-%d')
    if request.method == "POST":
        physician = request.POST.get('physician')
        mode = request.POST.getlist('mode_of_release')

    if 'Pick-Up' in mode and 'Email' in mode:
        mode_of_release = 'Both'
    else:
        mode_of_release = 'Pick-up' if 'Pick-Up' in mode else 'Email'
        
    lab_request = LabRequest.objects.create(
        patient=p,
        date_requested=current_date,
        physician=physician,
        mode_of_release=mode_of_release,
        overall_status="Not Started"
    )
    
    # Save selected components and packages in the request_line_item table
    for component in components:        
        RequestLineItem.objects.create(
            request=lab_request,
            component=component,
            template_used=component.template_id,
            request_status="Not Started"
        )
        # Fetch fields for this component’s template, excluding Labels
        sections = TemplateSection.objects.filter(template_id=component.template_id)
        for section in sections:
            fields = TemplateField.objects.filter(section=section).exclude(field_type='Label')
            for field in fields:
                ResultValue.objects.create(
                    line_item=RequestLineItem.objects.last(),
                    field=field,
                    field_value=''  # Initially blank
                )
    
    for package in packages:
        # Save each component of the package as a separate line item
        package_components = TestPackageComponent.objects.filter(package=package)
        for package_component in package_components:
            RequestLineItem.objects.create(
                request=lab_request,
                component=package_component.component,
                package=package,
                template_used=package_component.component.template_id,
                request_status="Not Started"
            )
            # Fetch fields for this component’s template, excluding Labels
            sections = TemplateSection.objects.filter(template_id=package_component.component.template_id)
            for section in sections:
                fields = TemplateField.objects.filter(section=section).exclude(field_type='Label')
                for field in fields:
                    ResultValue.objects.create(
                        line_item=RequestLineItem.objects.last(),
                        field=field,
                        field_value=''  # Initially blank
                    )
    
    return render(request, 'labreqsys/summarize_labreq.html', {
        'patient': p,
        'components': components,
        'packages': packages,
        'total': total,
        'date': current_date,
        'physician': physician,
        'mode_of_release': mode_of_release,
        'discount': discount,
        'request_id': lab_request.request_id  # Pass the request ID to the template
    })

def view_individual_lab_request(request, request_id):
    """
    Display detailed information about a specific lab request.
    """
    lab_request = get_object_or_404(LabRequest, pk=request_id)
    request_details = lab_request.get_request_details()
    return render(request, 'labreqsys/lab_request_details.html', {'request_details': request_details})


def add_lab_result(request, line_item_id):
    line_item = get_object_or_404(RequestLineItem, pk=line_item_id)
    test_component = get_object_or_404(TestComponent, pk=line_item.component_id)
    template = get_object_or_404(TemplateForm, pk=line_item.template_used)
    sections = TemplateSection.objects.filter(template_id=template.pk)
    
    section_data = []
    for s in sections:
        fields = TemplateField.objects.filter(section_id=s.pk)
        section_data.append({'section': s, 'fields': fields})

    lab_request = get_object_or_404(LabRequest, pk=line_item.request_id)
    patient = get_object_or_404(Patient, pk=lab_request.patient_id)
    lab_techs = LabTech.objects.all()

    return render(request, 'labreqsys/add_labresult.html', {
        'line_item': line_item,
        'template': template,
        'sections': section_data,
        'patient': patient,
        'request': lab_request,
        'test': test_component,
        'patient_name': 'Name Test',
        'patient_age': 'Age',
        'patient_address': 'Test Address',
        'lab_technicians': lab_techs
    })

def submit_labresults(request, line_item_id):
    # Retrieve the result values for this request
    results = ResultValue.objects.filter(line_item_id=line_item_id)
    if request.method == "POST":
        for r in results:
            field = TemplateField.objects.get(field_id=r.field_id)
            new_value = request.POST[field.label_name]
            r.field_value = new_value
            r.save()

    line_item = RequestLineItem.objects.get(line_item_id=results.first().line_item_id)
    line_item.request_status = 'Completed'
    line_item.save()
    return redirect('view_individual_lab_request', request_id=line_item.request_id)