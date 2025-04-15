from django.shortcuts import render, redirect, get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder
import json
from .models import Patient, LabRequest, CollectionLog, TestComponent, TemplateForm, TestPackage, TestPackageComponent, RequestLineItem, TemplateSection, TemplateField, LabTech, ResultValue, ResultReview
from datetime import date, datetime
from decimal import Decimal
from django.utils import timezone
from django.http import HttpResponse
from django.urls import reverse

import pdfkit
config=pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
import zipfile
import zipfile
from io import BytesIO
import os




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
    
    current_date = datetime.now().strftime('%Y-%m-%d')
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
    
    existing_results = ResultValue.objects.filter(line_item=line_item)
    result_dict = {res.field_id: res.field_value for res in existing_results}

    section_data = []
    for s in sections:
        fields = TemplateField.objects.filter(section_id=s.pk)
        for field in fields:
            field.saved_value = result_dict.get(field.field_id)
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
    results = ResultValue.objects.filter(line_item_id=line_item_id)
    if request.method == "POST":
        for r in results:
            field = TemplateField.objects.get(field_id=r.field_id)
            new_value = request.POST[field.label_name]
            r.field_value = new_value
            r.save()
        submission_type = request.POST.get('submission_type')

    line_item = RequestLineItem.objects.get(line_item_id=results.first().line_item_id)
    if submission_type == 'submit':
        line_item.request_status = 'Completed'
        line_item.progress_timestamp = timezone.now()
    else:
        line_item.request_status = 'In Progress'
    line_item.save()
    return redirect('view_individual_lab_request', request_id=line_item.request_id)
def add_patient (request):
    if request.method == "POST":
        last_name = request.POST.get('last_name')
        first_name = request.POST.get('first_name')
        middle_initial = request.POST.get('middle_initial')
        suffix = request.POST.get('suffix')
        sex = request.POST.get('sex')
        civil_status = request.POST.get('civil_status') 
        
        birthdate = request.POST.get('birthdate')
        
        # makes sure birthdate = None when birthdate is passed as "" from request.POST
        # i know it should be from the model parameters, but omg its not working TT~TT
        if birthdate == "":
            birthdate = None


        mobile_num = request.POST.get('mobile_num')
        
        # makes sure mobile_num = None when mobile_num is passed as "" from request.POST
        # i know it should be from the model parameters, but omg its not working TT~TT (2)
        if mobile_num == "":
            mobile_num = None
            
        # handles check statement in database
        elif mobile_num.startswith ("63") == False:
            mobile_num = "63" + mobile_num.lstrip("0")
                    
        
        landline_num = request.POST.get('landline_num')
        
        # makes sure landline_num = None when landline_num is passed as "" from request.POST
        # i know it should be from the model parameters, but omg its not working TT~TT (2)
        if landline_num == "":
            landline_num = None
        
        # handles check statement in database    
        elif landline_num.startswith("0") == False:
            landline_num = "0" + landline_num
        
        email = request.POST.get('email')
        if email == "":
            email = None
        
        house_num = request.POST.get('house_num')
        street = request.POST.get('street')
        baranggay = request.POST.get('baranggay')
        province = request.POST.get('province')
        city = request.POST.get('city')
        
        zip_code = request.POST.get('zip_code')
        if zip_code == "":
            zip_code = None
        
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
        return render(request, 'labreqsys/add_patient.html')


def pdf(request, pk):
    '''
        Webpage to format pdf!
    '''
    
    line_item = RequestLineItem.objects.get(line_item_id=pk)
    
    test_component = TestComponent.objects.get(component_id=line_item.component.component_id)
    
    template_form = TemplateForm.objects.get(template_id=test_component.template.template_id)
    
    lab_request = LabRequest.objects.get(request_id=line_item.request.request_id)

    patient = Patient.objects.get(patient_id=lab_request.patient.patient_id)
    
    
    template_section = TemplateSection.objects.filter(template=template_form.template_id)
    template_field = []
    result_value = []
    
    result_values = []

    for section in template_section:
        fields = TemplateField.objects.filter(section=section.section_id)
        for field in fields:
            template_field.append(field)
            results = ResultValue.objects.filter(line_item_id=line_item.line_item_id, field__field_id=field.field_id)
            for result in results:
                result_value.append(result)
    
    
    age = 0
    if patient.birthdate:
        today = date.today()
        age = today.year - patient.birthdate.year - ((today.month, today.day) < (patient.birthdate.month, patient.birthdate.day))
    else:
        age = None          
            
        
    
    
        
        

            
    
    # -----------------------
    # Text/Number Type
    template_sec_result = TemplateSection.objects.filter(template=template_form.template_id, section_name__icontains='results')
    template_field_result = None
    for result in template_sec_result:
        template_field_result=TemplateField.objects.filter(section=result.section_id)

    # Image Type
    template_sec_image = TemplateSection.objects.filter(template=template_form.template_id, section_name__icontains='image')
    template_field_image = None
    for image in template_sec_image: 
        template_field_image=TemplateField.objects.filter(section=image.section_id)
    
    # Remark Type
    template_sec_remark = TemplateSection.objects.filter(template=template_form.template_id, section_name__icontains='remarks')
    template_field_remark = None
    for remark in template_sec_remark: 
        template_field_remark=TemplateField.objects.filter(section=remark.section_id)
    
    
    
    for result in template_sec_result:
        result_value_result = ResultValue.objects.filter(line_item_id=line_item.line_item_id, field__section_id=result.section_id)
    
    for remark in template_sec_remark:
        result_value_remark = ResultValue.objects.filter(line_item_id=line_item.line_item_id, field__section_id=remark.section_id)

    # --------
    
    
    
    
    return render(request, 'labreqsys/pdf.html', 
                {'line_item':line_item,
                'test_component':test_component,
                'template_form':template_form,
                'template_section': template_section,
                'template_field': template_field, 
                
                
                #'template_sec_result': template_sec_result,
                #'template_sec_image': template_sec_image,
                #'template_sec_remark': template_sec_remark,
                #'template_field_result':template_field_result,
                #'template_field_image':template_field_image,
                #'template_field_remark':template_field_remark,
                'lab_request': lab_request, 
                'patient': patient, 
                'result_value': result_value,             
                #'result_value_result': result_value_result,
                #'result_value_remark': result_value_remark,
                # 'review_result': review_result,
                'age': age,
                'address': "testing",
                })


def generatePDF(request):
    '''
    Request to generate PDF
    '''
    ids = request.GET.get("ids", "").split(",") 
    pdfs = []
    filenames = []

    if len(ids) > 1: # Return zip with all pdfs selected
        for pk in ids:
            try:
                pdf_response = savePDF(request, pk)
                pdfs.append(pdf_response)
                filenames.append(f"patient_{pk}.pdf")
            except Patient.DoesNotExist:
                print(f"Patient with ID {pk} does not exist.")
                continue
            except Exception as e:
                print(f"Error generating PDF for ID {pk}: {e}")
                continue

        if not pdfs:
            return HttpResponse("No PDFs were generated.", status=400)

        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for pdf_response, filename in zip(pdfs, filenames):
                zip_file.writestr(filename, pdf_response.content)

        zip_buffer.seek(0)

        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="patients_pdfs.zip"'
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
    print (f"pdf: {line_item}")
    
    filename = f"{line_item.request.patient.last_name}_{line_item.component.test_name}_{line_item.request.date_requested}.pdf"
    # Create PDF from URL (the URL will be a page where you render patient details)
    pdf = pdfkit.from_url(request.build_absolute_uri(reverse('pdf', args=[pk])), False)
    
    # Return the PDF response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'  # Correct filename usage
    print("PDF made")

    return response