from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
import json
from .models import Patient, LabRequest, CollectionLog, TestComponent, TemplateForm, TestPackage, TestPackageComponent, RequestLineItem, TemplateSection, TemplateField, LabTech, ResultValue, ResultReview
from django.db.models import Q
from datetime import date, datetime
from decimal import Decimal
from django.utils import timezone
from django.http import HttpResponse
from django.urls import reverse
from .forms import LabTechForm, EditLabTechForm

import pdfkit
import platform
import zipfile
import zipfile
from io import BytesIO
import os
import decimal
from django.db.models import Max

from django.views.decorators.clickjacking import xframe_options_exempt

# Determine wkhtmltopdf path based on OS
if platform.system() == 'Windows':
    wkhtmltopdf_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
else:  # macOS and Linux
    wkhtmltopdf_path = '/usr/local/bin/wkhtmltopdf'  # Default Homebrew installation path

config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)

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

def testComponents(request):
    """
    Display a list of all test components.
    """
    testComponents = TestComponent.objects.all()
    
    return render(request, 'labreqsys/testComponents.html', {'testComponents': testComponents})

def view_patient(request, pk):
    """
    Display detailed information about a specific patient.
    """
    p = get_object_or_404(Patient, pk=pk)
    full_name = f"{p.last_name}, {p.first_name} {p.middle_initial} {p.suffix}"

    if p.birthdate:
        today = date.today()
        age = today.year - p.birthdate.year - ((today.month, today.day) < (p.birthdate.month, p.birthdate.day))
    else:
        age = None
        
    address_append = []
    
    
    if p.street:
        address_append.append(p.street)
    if p.subdivision:
        address_append.append(p.subdivision)
    if p.baranggay:
        address_append.append(p.baranggay)
    if p.city:
        address_append.append(p.city)
    if p.province:
        address_append.append(p.province)
    if p.zip_code:
        address_append.append(p.zip_code)
    
    address = ', '.join(address_append) if address_append else None
    
    if p.house_num:
        address = f"{p.house_num} {address}"

    lab_requests = LabRequest.objects.filter(patient=p)
    request_details = []

    for req in lab_requests:
        pickup_status = 'N/A'
        email_status = 'N/A'

        if req.mode_of_release in ['Pick-up', 'Both']:
            c = CollectionLog.objects.get(request=req, mode_of_collection='Pick-up')
            if c.time_collected is None:
                pickup_status = 'Uncollected'
            elif c.time_collected:
                pickup_status = 'Collected'

        if req.mode_of_release in ['Email', 'Both']:
            c = CollectionLog.objects.get(request=req, mode_of_collection='Email')
            if c.time_collected is None:
                email_status = 'Not Sent'
            elif c.time_collected:
                email_status = 'Sent'

        request_details.append({
            'request_id': req.request_id,
            'date_requested': req.date_requested,
            'overall_status': req.overall_status,
            'pickup_status': pickup_status,
            'email_status': email_status,
        })

    return render(request, 'labreqsys/view_patient.html', {
        'patient': p,
        'full_name': full_name,
        'age': age,
        'address': address,  # Replace with actual address
        'requests': request_details
    })

def add_testcomponent(request):
    """
    Display a form to add a new test component.
    """
    return render(request, 'labreqsys/add_testcomponent.html')

def add_template(request):
    """
    Display form builder to create a template.
    """
    return render(request, 'labreqsys/add_template.html')

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
    # Handle empty session data
    sc = request.session.get('selected_components', []) or []
    sp = request.session.get('selected_packages', []) or []
    
    subtotal = Decimal('0.00')  # Initialize subtotal
    components = []
    packages = []
    
    # Safely handle component prices
    for t in sc:
        try:
            temp = get_object_or_404(TestComponent, pk=t)
            subtotal += Decimal(str(temp.component_price or 0))  # Add to subtotal
            components.append(temp)
        except (ValueError, TypeError):
            subtotal += Decimal('0.00')
            
    # Safely handle package prices
    for t in sp:
        try:
            temp = get_object_or_404(TestPackage, pk=t)
            subtotal += Decimal(str(temp.package_price or 0))  # Add to subtotal
            packages.append(temp)
        except (ValueError, TypeError):
            subtotal += Decimal('0.00')
        
    discount = Decimal('0.00')
    total = subtotal  # Initialize total with subtotal
    
    # Apply discount only if patient has a non-empty PWD ID or Senior ID
    has_pwd = p.pwd_id_num and str(p.pwd_id_num).strip()
    has_senior = p.senior_id_num and str(p.senior_id_num).strip()
    if has_pwd or has_senior:
        try:
            discount = round(subtotal * Decimal('0.2'), 2)
            total = subtotal - discount
        except (ValueError, TypeError, decimal.InvalidOperation):
            discount = Decimal('0.00')
    
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Safely get next request ID
    try:
        last_request = LabRequest.objects.order_by('-request_id').first()
        next_request_id = (last_request.request_id + 1) if last_request else 1
    except Exception:
        # Fallback to a query that gets the max ID directly
        next_request_id = (LabRequest.objects.aggregate(Max('request_id'))['request_id__max'] or 0) + 1

    if request.method == "POST":
        physician = request.POST.get('physician', '').strip() or None
        # This is the initial submission from add_labreq_details
        mode = request.POST.getlist('mode_of_release')

        #KEEP THIS WHEN U ARE MERGING, THIS IS THE MOST UPDATED
        if not mode:  # If no mode selected, default to Pick-up
            mode_of_release = 'Pick-up'
        elif 'Pick-up' in mode and 'Email' in mode:  # If both selected
            mode_of_release = 'Both'
        elif 'Email' in mode:  # If only Email selected
            mode_of_release = 'Email'
        else:  # If only Pick-up selected
            mode_of_release = 'Pick-up'

        if "confirm" in request.POST and request.POST["confirm"] == "submit":
            # Only proceed if we have components or packages
            final_mode = request.POST.get('mode_of_release')
            if components or packages:
                lab_request = LabRequest.objects.create(
                    request_id=next_request_id,
                    patient=p,
                    date_requested=current_date,
                    physician=physician,
                    mode_of_release=final_mode,
                    overall_status="Not Started"
                )

                if 'Both' in mode or 'Pick-up' in mode:
                    CollectionLog.objects.create(
                        request = lab_request,
                        mode_of_collection = 'Pick-up'
                    )
                if 'Both' in mode or 'Email' in mode:
                    CollectionLog.objects.create(
                        request = lab_request,
                        mode_of_collection = 'Email'
                    )
                
                for component in components:
                    try:
                        RequestLineItem.objects.create(
                            request=lab_request,
                            component=component,
                            request_status="Not Started",
                            template_used=component.template_id
                        )

                        # Fetch fields for this component's template, excluding Labels
                        sections = TemplateSection.objects.filter(template_id=component.template_id)
                        for section in sections:
                            fields = TemplateField.objects.filter(section=section).exclude(field_type='Label')
                            for field in fields:
                                ResultValue.objects.create(
                                    line_item=RequestLineItem.objects.last(),
                                    field=field,
                                    field_value= ''
                                )
                    except Exception:
                        continue  # Skip this item if there's an error
                
                for package in packages:
                    try:
                        package_components = TestPackageComponent.objects.filter(package=package)
                        for package_component in package_components:
                            RequestLineItem.objects.create(
                                request=lab_request,
                                component=package_component.component,
                                package=package,
                                request_status="Not Started",
                                template_used=package_component.component.template_id
                            )
                            # Fetch fields for this component's template, excluding Labels
                            sections = TemplateSection.objects.filter(template_id=package_component.component.template_id)
                            for section in sections:
                                fields = TemplateField.objects.filter(section=section).exclude(field_type='Label')
                                for field in fields:
                                    ResultValue.objects.create(
                                        line_item=RequestLineItem.objects.last(),
                                        field=field,
                                        field_value=''  # Initially blank
                                    )
                    except Exception:
                        continue  # Skip this package if there's an error
            
            return redirect('view_patient', pk=pk)
        elif "confirm" in request.POST and request.POST["confirm"] == "cancel":
            return redirect('view_patient', pk=pk)
    else:
        physician = None
        mode_of_release = None

    # Render the summary page
    return render(request, 'labreqsys/summarize_labreq.html', {
        'patient': p,
        'components': components,
        'packages': packages,
        'total': total,
        'subtotal': subtotal,
        'date': current_date,
        'discount': discount,
        'physician': physician,
        'mode_of_release': mode_of_release,
        'request_id': next_request_id
    })

def view_individual_lab_request(request, request_id):
    """
    Display detailed information about a specific lab request.
    """
    lab_request = get_object_or_404(LabRequest, pk=request_id)
    request_details = lab_request.get_request_details()
    collection_status = ''
    email_status = ''
    if lab_request.mode_of_release == 'Both' or lab_request.mode_of_release == 'Pick-up':
        c = CollectionLog.objects.get(request=lab_request, mode_of_collection='Pick-up')
        if c.time_collected is None:
            collection_status = 'Uncollected'
        else:
            collection_status = 'Collected'
    if lab_request.mode_of_release == 'Both' or lab_request.mode_of_release == 'Email':
        c = CollectionLog.objects.get(request=lab_request, mode_of_collection='Email')
        if c.time_collected is None:
            email_status = 'Not Sent'
        else:
            email_status = 'Sent'

    return render(request, 'labreqsys/lab_request_details.html', {'request_details': request_details, 'collection_status': collection_status, 'email_status': email_status})

def change_collection_status(request, request_id):
    """
    Change email or collection status
    """
    c_mode = ''
    e_mode= ''
    print(request.method)
    if request.method == "POST":
        lab_request = get_object_or_404(LabRequest, pk=request_id)
        c_mode = request.POST.get('collected')
        e_mode = request.POST.get('emailed')
        try:
            if 'Collected' in c_mode:
                c = CollectionLog.objects.get(request=lab_request, mode_of_collection='Pick-up')
                c.time_collected=timezone.now()
                c.save()
        except:
            if 'Sent' in e_mode:
                c = CollectionLog.objects.get(request=lab_request, mode_of_collection='Email')
                c.time_collected=timezone.now()
                c.save()
    return redirect('view_individual_lab_request', request_id=request_id)

def add_lab_result(request, line_item_id):
    line_item = get_object_or_404(RequestLineItem, pk=line_item_id)
    test_component = get_object_or_404(TestComponent, pk=line_item.component_id)
    template = get_object_or_404(TemplateForm, pk=line_item.template_used)
    sections = TemplateSection.objects.filter(template_id=template.pk)
    
    existing_results = ResultValue.objects.filter(line_item=line_item)
    result_dict = {res.field_id: res.field_value for res in existing_results}

    section_data = []
    for s in sections:
        fields = TemplateField.objects.filter(section_id=s.pk)
        field_count = 0
        for field in fields:
            field.saved_value = result_dict.get(field.field_id)
            field_count+=1
        section_data.append({'section': s, 'field_count': field_count, 'fields': fields})

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
    results = ResultValue.objects.filter(line_item_id=line_item_id)

    if request.method == "POST":
        for r in results:
            field = TemplateField.objects.get(field_id=r.field_id)
            new_value = request.POST[field.label_name]
            r.field_value = new_value
            r.save()
        submission_type = request.POST.get('submission_type')

    line_item = RequestLineItem.objects.get(line_item_id=results.first().line_item_id)
    lab = LabRequest.objects.get(request_id=line_item.request_id)
    
    if submission_type == 'submit':
        line_item.request_status = 'Completed'
        line_item.progress_timestamp = timezone.now()
        line_item.save()

        lineitems = RequestLineItem.objects.filter(request=lab.request_id)
        temp = []
        if lab.overall_status == 'Not Started' or lab.overall_status == 'In Progress':
            for l in lineitems:
                temp.append(l.request_status)
            if 'Not Started' not in temp and 'In Progress' not in temp:
                lab.overall_status = 'Completed'
                lab.save()
            elif lab.overall_status == 'Not Started':
                lab.overall_status = 'In Progress'
                lab.save()
        
    else:
        line_item.request_status = 'In Progress'
        line_item.save()
            
        if lab.overall_status == 'Not Started':
            lab.overall_status = 'In Progress'
            lab.save()


    return redirect('view_individual_lab_request', request_id=line_item.request_id)

def add_patient (request):
    '''
    
    Takes add patients, then processes for formatting
    
    '''
    if request.method == "POST":
        last_name = request.POST.get('last_name')
        first_name = request.POST.get('first_name')
        middle_initial = request.POST.get('middle_initial')
        suffix = request.POST.get('suffix')
        sex = request.POST.get('sex')
        civil_status = request.POST.get('civil_status') 
        birthdate = request.POST.get('birthdate')
        
        mobile_num = request.POST.get('mobile_num')
        # handles check statement in database
        if mobile_num != "" and mobile_num.startswith ("63") == False :
            mobile_num = "63" + mobile_num.lstrip("0")
        
        landline_num = request.POST.get('landline_num')

        email = request.POST.get('email')
        house_num = request.POST.get('house_num')
        street = request.POST.get('street')
        baranggay = request.POST.get('baranggay')
        subdivision = request.POST.get('subdivision')
        province = request.POST.get('province')
        city = request.POST.get('city')
        zip_code = request.POST.get('zip_code')
        pwd_id_num = request.POST.get('pwd_id_num')
        senior_id_num = request.POST.get('senior_id_num')
        
        query = Q(first_name__exact=first_name, last_name__exact=last_name, birthdate__exact=birthdate, sex=sex, city__exact=city)
        
        if mobile_num:
            query |= Q(mobile_num__icontains=mobile_num)
        if landline_num:
            query |= Q(landline_num__icontains=landline_num)
        if email:
            query |= Q(email__icontains=email)

        
        if Patient.objects.filter(query).exists():
            messages.error(request, "Patient already exists.")
            return redirect('patientList')
        else:    
            return render(request, 'labreqsys/add_patient_details.html', {
                'last_name':last_name,
                'first_name':first_name,
                'middle_initial':middle_initial,
                'suffix':suffix,
                'sex':sex,
                'civil_status':civil_status,
                'birthdate':birthdate,
                'mobile_num':mobile_num,
                'landline_num':landline_num,
                'email':email,
                'house_num':house_num,
                'street':street,
                'subdivision':subdivision,
                'baranggay':baranggay,
                'province':province,
                'city':city,
                'zip_code':zip_code,
                'pwd_id_num':pwd_id_num,
                'senior_id_num':senior_id_num,
                'modal': True})
    else:
        return render(request, 'labreqsys/add_patient.html')
    

def add_patient_details(request):
    '''
    
    Displays preview of Add Patient details, then saves
    
    '''    
    if request.method == "POST":
        last_name = request.POST.get('last_name')      
        first_name = request.POST.get('first_name')
        middle_initial = request.POST.get('middle_initial')
        suffix = request.POST.get('suffix')
        sex = request.POST.get('sex')
        civil_status = request.POST.get('civil_status') 
        birthdate = request.POST.get('birthdate')
        mobile_num = request.POST.get('mobile_num')
        landline_num = request.POST.get('landline_num')
        email = request.POST.get('email')
        house_num = request.POST.get('house_num')
        street = request.POST.get('street')
        baranggay = request.POST.get('baranggay')
        province = request.POST.get('province')
        city = request.POST.get('city')
        subdivision = request.POST.get('subdivision')
        zip_code = request.POST.get('zip_code')
        pwd_id_num = request.POST.get('pwd_id_num')
        senior_id_num = request.POST.get('senior_id_num')
        
        query = Q(first_name__exact=first_name, last_name__exact=last_name, birthdate__exact=birthdate, sex=sex, city__exact=city)
        
        if mobile_num:
            query |= Q(mobile_num__icontains=mobile_num)
        if landline_num:
            query |= Q(landline_num__icontains=landline_num)
        if email:
            query |= Q(email__icontains=email)

        
        if Patient.objects.filter(query).exists():
            messages.error(request, "Patient already exists.")
            return redirect('patientList')
        else:
            new_p = Patient.objects.create(
                        last_name=last_name,
                        first_name=first_name,
                        middle_initial=middle_initial,
                        suffix=suffix,
                        sex=sex,
                        civil_status=civil_status,
                        birthdate=birthdate,
                        mobile_num=mobile_num,
                        landline_num=landline_num,
                        email=email,
                        house_num=house_num,
                        street=street,
                        baranggay=baranggay,
                        province=province,
                        city=city,
                        zip_code=zip_code,
                        pwd_id_num=pwd_id_num,
                        senior_id_num=senior_id_num
                        )
        
            p = Patient.objects.get(pk=new_p.patient_id)
            return redirect('view_patient', pk=p.pk)   
    else:
        return render(request, 'labreqsys/add_patient_details.html')

def save_patient(request):
    if request.method == "POST":
        last_name = request.POST.get('last_name')
        print(f"ast:{last_name}")
        
        first_name = request.POST.get('first_name')
        middle_initial = request.POST.get('middle_initial')
        suffix = request.POST.get('suffix')
        sex = request.POST.get('sex')
        civil_status = request.POST.get('civil_status') 
        birthdate = request.POST.get('birthdate')
        mobile_num = request.POST.get('mobile_num')
        landline_num = request.POST.get('landline_num')
        email = request.POST.get('email')
        house_num = request.POST.get('house_num')
        street = request.POST.get('street')
        baranggay = request.POST.get('baranggay')
        province = request.POST.get('province')
        city = request.POST.get('city')
        subdivision = request.POST.get('subdivision')
        zip_code = request.POST.get('zip_code')
        pwd_id_num = request.POST.get('pwd_id_num')
        senior_id_num = request.POST.get('senior_id_num')
    
        new_p = Patient.objects.create(
                    last_name=last_name,
                    first_name=first_name,
                    middle_initial=middle_initial,
                    suffix=suffix,
                    sex=sex,
                    civil_status=civil_status,
                    birthdate=birthdate,
                    mobile_num=mobile_num,
                    landline_num=landline_num,
                    email=email,
                    house_num=house_num,
                    street=street,
                    baranggay=baranggay,
                    province=province,
                    city=city,
                    zip_code=zip_code,
                    pwd_id_num=pwd_id_num,
                    senior_id_num=senior_id_num
                    )
            
        p = Patient.objects.get(pk=new_p.patient_id)
        return redirect('view_patient', pk=p.pk)
    else: 
        return HttpResponse ("dumbass bitch?")
    
@xframe_options_exempt
def pdf(request, pk):
    '''
        Webpage to format pdf!
    '''
    
    line_item = RequestLineItem.objects.get(line_item_id=pk)

    test_component = TestComponent.objects.get(component_id=line_item.component.component_id)

    template_form = TemplateForm.objects.filter(template_id=line_item.component.template.template_id).order_by('-template_id')[0]
    # Looks for the latest template made

    lab_request = LabRequest.objects.get(request_id=line_item.request.request_id)

    patient = Patient.objects.get(patient_id=lab_request.patient.patient_id)


    # [MADS NOTES]: CHAOS ENSUES !

    ''' 
        !! form 'dict' will look like this:
        {
            <TemplateSection 1>: --> Represents a row #1
                {
                    TemplateField 1 : Results[],                --> Represents field_value already filled
                    TemplateField 2 : Results[<ResultValue 1>]  --> Represents field_value filled in by user
                    TemplateField 3 : Results[]                 --> Ex. Unit, Field_value = g/L
                    TemplateField 4 : Results[<ResultValue 2>]  --> Ex. Result, Field_value = 12 (INPUT)
                }
            <TemplateSection 2>: --> Represents a row #2
                {
                    TemplateField 2 : Results[<ResultValue 1>]  --> Ex. Remarks, Field_value = "Neutral" (INPUT)
                }
        }
        
        This way, its easier to map out results with user input and a lot more dynamic
    '''

    form = {}
    fields = []
    reviewed_by = [] # [MADS TO DO!] When ResultReview starts saving, pass reviewer data here

    template_section = TemplateSection.objects.filter(template=template_form.template_id)

    for section in template_section:
        fields.append(TemplateField.objects.filter(section=section.section_id)) # list of all fields per section and appends to fields 'list'

        for column in fields:
            result_value = {}
            for field in column:
                result_value[field] = ResultValue.objects.filter(line_item_id=line_item.line_item_id, field__field_id=field.field_id)
        form[section] = result_value # pairs result_value 'dict' to a section 'queryset' 

    results = ResultValue.objects.filter(line_item_id=line_item.line_item_id)
    reviews = []

    for rs in results:
        review = ResultReview.objects.filter(result_value=rs)
        print(f"{rs} + {len(results)}")
        for lt in review:
            print(f"review: {lt}")
            if not reviews:
                reviews.append(lt)
                print("yes 1\n")
            else:
                for rev in reviews:
                    print(f"rev : {rev.lab_tech.lab_tech_id}; lt : {lt.lab_tech.lab_tech_id}")
                    if lt.lab_tech.lab_tech_id != rev.lab_tech.lab_tech_id:
                        print ("yes 2\n")
                        reviews.append(lt)
                    else:
                        print("no\n")
                        break
    print (f"review!: {reviews}")

    age = 0
    if patient.birthdate:
        today = date.today()
        age = today.year - patient.birthdate.year - ((today.month, today.day) < (patient.birthdate.month, patient.birthdate.day))
    else:
        age = None                 

    return render(request, 'labreqsys/pdf.html', 
                {'lab_request': lab_request, 
                'patient': patient, 
                'test_component':test_component,
                'age': age,
                'address': "testing",
                'form' : form,
                'reviewed_by': reviewed_by,
                'lab_tech' : reviews               
                })


def generatePDF(request):
    '''
    Request to generate PDF
    '''
    ids = request.GET.get("ids", "").split(",") 
    
    if len(ids) > 1: # Return zip with all pdfs selected
        pdfs = []
        filenames = []
        for pk in ids:
            try:
                line_item = RequestLineItem.objects.get(line_item_id=pk)
                filename = f"{line_item.request.patient.last_name}, {line_item.request.patient.first_name[0]}_{line_item.component.test_name}_{line_item.request.date_requested}.pdf"
                
                pdf_response = savePDF(request, pk)
                pdfs.append(pdf_response)
                filenames.append(filename)
            except Patient.DoesNotExist:
                print(f"Patient with ID {pk} does not exist.")
                continue
            except Exception as e:
                print(f"Error generating PDF for ID {pk}: {e}")
                continue
            
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for pdf_response, filename in zip(pdfs, filenames):
                zip_file.writestr(filename, pdf_response.content)

        zip_buffer.seek(0)
        
        filename_z = f"{line_item.request.patient.last_name}_{line_item.request.date_requested}.zip"

        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename_z}"'
        return response
    elif len(ids) == 1: # Return only one pdf
        return savePDF(request, ids[0])

    return HttpResponse("No PDFs.")
    

# PDF generation function for a single patient
def savePDF(request, pk):
    '''
    Save PDF using pdfkit
    '''
    
    line_item = RequestLineItem.objects.get(line_item_id=pk)
    
    filename = f"{line_item.request.patient.last_name}, {line_item.request.patient.first_name[0]}_{line_item.component.test_name}_{line_item.request.date_requested}.pdf"
    # Create PDF from URL (the URL will be a page where you render patient details)
    pdf = pdfkit.from_url(request.build_absolute_uri(reverse('pdf', args=[pk])), False)
    
    # Return the PDF response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'  # Correct filename usage

    return response

def add_lab_tech(request):
    """
    Handle the addition of a new lab technician.
    """
    if request.method == 'POST':
        form = LabTechForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                lab_tech = form.save(commit=False)
                
                # Handle signature file
                signature = form.cleaned_data['signature']
                # Create a unique filename using timestamp and tech's name
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_name = "".join(c for c in lab_tech.last_name if c.isalnum())
                filename = f"signature_{safe_name}_{timestamp}.png"
                
                # Save the signature file
                file_path = os.path.join('labreqsys', 'static', 'signatures', filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'wb+') as destination:
                    for chunk in signature.chunks():
                        destination.write(chunk)
                
                # Save the path to the database
                lab_tech.signature_path = f'signatures/{filename}'
                lab_tech.save()
                
                messages.success(request, 'Lab technician added successfully!')
                return redirect('view_lab_techs')
            except Exception as e:
                # If something goes wrong with file handling
                messages.error(request, f'Error saving lab technician: {str(e)}')
                # Try to clean up the file if it was created
                if 'file_path' in locals():
                    try:
                        os.remove(file_path)
                    except:
                        pass
    else:
        form = LabTechForm()
    
    return render(request, 'labreqsys/add_lab_tech.html', {'form': form})

def view_lab_techs(request):
    """
    Display a list of all lab technicians.
    """
    lab_techs = LabTech.objects.all()
    return render(request, 'labreqsys/view_lab_techs.html', {'lab_techs': lab_techs})

def edit_lab_tech(request, lab_tech_id):
    """
    Handle editing of an existing lab technician.
    """
    lab_tech = get_object_or_404(LabTech, pk=lab_tech_id)
    
    if request.method == 'POST':
        form = EditLabTechForm(request.POST, request.FILES, instance=lab_tech)
        if form.is_valid():
            try:
                lab_tech = form.save(commit=False)
                
                # Handle signature file if provided
                if 'signature' in request.FILES:
                    signature = request.FILES['signature']
                    # Create a unique filename using timestamp and tech's name
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    safe_name = "".join(c for c in lab_tech.last_name if c.isalnum())
                    filename = f"signature_{safe_name}_{timestamp}.png"
                    
                    # Save the signature file
                    file_path = os.path.join('labreqsys', 'static', 'signatures', filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # Delete old signature file if it exists
                    if lab_tech.signature_path:
                        old_path = os.path.join('labreqsys', 'static', lab_tech.signature_path)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    
                    with open(file_path, 'wb+') as destination:
                        for chunk in signature.chunks():
                            destination.write(chunk)
                    
                    # Update the path in the database
                    lab_tech.signature_path = f'signatures/{filename}'
                
                lab_tech.save()
                messages.success(request, 'Lab technician updated successfully!')
                return redirect('view_lab_techs')
            except Exception as e:
                messages.error(request, f'Error updating lab technician: {str(e)}')
                # Try to clean up the new file if it was created
                if 'file_path' in locals():
                    try:
                        os.remove(file_path)
                    except:
                        pass
    else:
        form = EditLabTechForm(instance=lab_tech)
    
    return render(request, 'labreqsys/edit_lab_tech.html', {
        'form': form,
        'lab_tech': lab_tech
    })
def view_lab_result(request, pk):
    """
    Display form builder to create a template.
    """
    line_item = get_object_or_404(RequestLineItem, line_item_id=pk)
    return render(request, 'labreqsys/view_lab_results.html', {'line_item' : line_item})


def packages (request):
    '''
    Display packages
    '''
    packages = TestPackage.objects.all()
    pc = TestPackageComponent.objects.all()
    return render(request, 'labreqsys/packages.html', {'packages': packages, 'pc': pc})

def add_package (request):
    '''
    Display packages
    '''
    test_components = TestComponent.objects.all()
    
    if request.method == "POST":
        package_name = request.POST.get('package_name')
        price = request.POST.get('price')
        components = request.POST.getlist('componentCheckbox')
        
        if TestPackage.objects.filter(package_name=package_name).exists():
            return redirect('packages')
        else:
            package = TestPackage.objects.create(
                package_name=package_name,
                package_price=price
                )
            
            for c in components:
                component = TestComponent.objects.get(component_id=c)
                TestPackageComponent.objects.create(
                    package=package,
                    component=component
                )

        return redirect('packages')
    else:
        return render(request, 'labreqsys/add_package.html', {'components': test_components})
