from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
import json
from .models import Patient, LabRequest, CollectionLog, TestComponent, TemplateForm, TestPackage, TestPackageComponent, RequestLineItem, TemplateSection, TemplateField, LabTech, ResultValue, ResultReview, UserProfile, EditPatientPasscode
from django.db.models import Q
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.urls import reverse
from .forms import LabTechForm, EditLabTechForm, UserRegistrationFormWithLabTech, CustomAuthenticationForm, EditReceptionistProfileForm, EditLabTechProfileForm
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from functools import wraps
from django.template.loader import render_to_string
from django.db.models import Count
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.deprecation import MiddlewareMixin

import pdfkit
import platform
import zipfile
from io import BytesIO
import os
import decimal
from django.db.models import Max
from django.db.models.functions import TruncDate
from django.views.decorators.clickjacking import xframe_options_exempt
from collections import defaultdict, OrderedDict


import random
from django.core.cache import cache
from django.views.decorators.http import require_GET

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

def delete_unused_templates():
    #delete the templates that were not used
    unused_forms = []
    past_records = list(RequestLineItem.objects.values_list('template_used', flat=True))
    temp = TemplateForm.objects.filter(testcomponent__isnull=True).values_list('template_id', flat=True)
    for t in temp:
        if t not in past_records:
            unused_forms.append(TemplateForm.objects.get(template_id=t))

    unused_sections = TemplateSection.objects.filter(template__in=unused_forms)
    unused_fields = TemplateField.objects.filter(section__in=unused_sections)

    unused_fields.delete()
    unused_sections.delete()
    for obj in unused_forms:
        obj.delete()

# Decorators
def owner_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check 1: Authentication
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return render(request, 'labreqsys/forbidden.html', {
                'message': "Authentication required to access this page.",
                'user': getattr(request, 'user', None) # Pass user if available
            }, status=403)

        # Check 2: Superuser Status (Grants immediate access)
        if getattr(request.user, 'is_superuser', False):
            return view_func(request, *args, **kwargs)

        # Check 3: Owner Role via UserProfile (Only if not superuser)
        try:
            if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'owner':
                return view_func(request, *args, **kwargs)
            else:
                # Has profile but not owner role
                return render(request, 'labreqsys/forbidden.html', {
                    'message': "You do not have Owner permissions for this page.",
                    'user': request.user
                }, status=403)
        except (UserProfile.DoesNotExist, AttributeError):
            # No profile found or attribute error
            return render(request, 'labreqsys/forbidden.html', {
                'message': "User profile not found or inaccessible; Owner permissions required.",
                'user': request.user
            }, status=403)
            
    return _wrapped_view

def receptionist_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        
        print("User:", user)
        print("Authenticated:", user.is_authenticated)
        print("Has profile:", hasattr(user, 'userprofile'))
        if hasattr(user, 'userprofile'):
            print("Role:", user.userprofile.role)
        
        if not user.is_authenticated:
            return render(request, 'labreqsys/forbidden.html', {
                'message': "You must be logged in to access this page.",
                'user': user
            }, status=403)
        if getattr(user, 'is_superuser', False):
            return view_func(request, *args, **kwargs) # Superusers are implicitly owners/all roles
        try:
            if hasattr(user, 'userprofile') and user.userprofile.role in ['receptionist', 'owner']:
                return view_func(request, *args, **kwargs)
        except (UserProfile.DoesNotExist, AttributeError):
            pass        
        return render(request, 'labreqsys/forbidden.html', {
            'message': "You do not have receptionist permissions to access this page.",
            'user': user
        }, status=403)
    

    return _wrapped_view

def lab_tech_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return render(request, 'labreqsys/forbidden.html', {
                'message': "You must be logged in to access this page.",
                'user': user
            }, status=403)
        if getattr(user, 'is_superuser', False):
            return view_func(request, *args, **kwargs) # Superusers are implicitly owners/all roles
        try:
            if hasattr(user, 'userprofile') and user.userprofile.role in ['lab_tech', 'owner']:
                return view_func(request, *args, **kwargs)
        except (UserProfile.DoesNotExist, AttributeError):
            pass   
        return render(request, 'labreqsys/forbidden.html', {
            'message': "You do not have lab technician permissions to access this page.",
            'user': user
        }, status=403)
    return _wrapped_view

def receptionist_or_lab_tech_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check 1: Authentication
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return render(request, 'labreqsys/forbidden.html', {
                'message': "Authentication required to access this page.",
                'user': getattr(request, 'user', None)
            }, status=403)

        # Check 2: Superuser Status (Grants immediate access)
        if getattr(request.user, 'is_superuser', False):
            return view_func(request, *args, **kwargs)

        # Check 3: Allowed Roles via UserProfile (Only if not superuser)
        try:
            allowed_roles = ['receptionist', 'lab_tech', 'owner']
            if hasattr(request.user, 'userprofile') and request.user.userprofile.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                # Has profile but not an allowed role
                return render(request, 'labreqsys/forbidden.html', {
                    'message': "You do not have the required permissions (Receptionist or Lab Technician) for this page.",
                    'user': request.user
                }, status=403)
        except (UserProfile.DoesNotExist, AttributeError):
            # No profile found or attribute error
            return render(request, 'labreqsys/forbidden.html', {
                'message': "User profile not found or inaccessible; Required permissions missing.",
                'user': request.user
            }, status=403)

    return _wrapped_view

def labtech_profile_complete_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        # Only enforce for lab techs (not owners, receptionists, or superusers)
        if user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.role == 'lab_tech':
            from .models import LabTech
            try:
                labtech = LabTech.objects.get(user=user)
                if not labtech.signature_path and request.resolver_match.url_name not in [
                    'complete_labtech_profile', 'edit_user_profile', 'logout', 'user_logout']:
                    return redirect('complete_labtech_profile')
            except LabTech.DoesNotExist:
                if request.resolver_match.url_name not in [
                    'complete_labtech_profile', 'edit_user_profile', 'logout', 'user_logout']:
                    return redirect('complete_labtech_profile')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# View functions
def base(request):
    """
    Render the base template.
    """
    return render(request, 'labreqsys/base.html')

@receptionist_or_lab_tech_required
def view_labreqs(request):
    """
    Display a list of all lab requests.
    """
    labreqs = LabRequest.objects.all()
    return render(request, 'labreqsys/view_labreqs.html', {'labreqs': labreqs})

@receptionist_required
def patientList(request):
    """
    Display a list of all patients.
    """
    patients = Patient.objects.all()
    return render(request, 'labreqsys/patientList.html', {'patients': patients})

@receptionist_or_lab_tech_required
def labRequests(request, requested_status):
    """
    Display a list of all lab requests.
    """
    today = date.today()
    yesterday = date.today() - timedelta(days=1)
    
    if requested_status == 0:
        labreqs = LabRequest.objects.select_related('patient').all()
    elif requested_status == 1:
        labreqs = LabRequest.objects.filter(overall_status='Not Started').select_related('patient')
    elif requested_status == 2:
        labreqs = LabRequest.objects.filter(overall_status='In Progress').select_related('patient')
    elif requested_status == 3:
        labreqs = LabRequest.objects.filter(overall_status='Completed').select_related('patient')
    elif requested_status == 4:
        labreqs = LabRequest.objects.filter(overall_status='Released').select_related('patient')
    
    lab_requests_by_date = defaultdict(list)

    sort_order = request.GET.get('sortby', 'latest')
    reverse_sort = True if sort_order == 'latest' else False
    
    if sort_order == 'latest':
        for r in reversed(labreqs):
            lab_requests_by_date[r.date_requested].append(r)
    else:
        for r in labreqs:
            lab_requests_by_date[r.date_requested].append(r)

    
    ordered_lab_requests = OrderedDict()

    if today in lab_requests_by_date:
        ordered_lab_requests[today] = lab_requests_by_date.pop(today)

    if yesterday in lab_requests_by_date:
        ordered_lab_requests[yesterday] = lab_requests_by_date.pop(yesterday)

    for date_key in sorted(lab_requests_by_date.keys(), reverse=reverse_sort):
        ordered_lab_requests[date_key] = lab_requests_by_date[date_key]

    return render(request, 'labreqsys/labRequests.html', {
        'labreqs': labreqs,
        'today': today,
        'yesterday': yesterday,
        'ordered_lab_requests': ordered_lab_requests})

@owner_required
def testComponents(request):
    """
    Display a list of all test components.
    """
    request.session.pop('testcomponent_form_data', None)
    testComponents = TestComponent.objects.all()
    delete_unused_templates()
    return render(request, 'labreqsys/testComponents.html', {'testComponents': testComponents})

@receptionist_required
def view_patient(request, pk):
    """
    Display detailed information about a specific patient.
    """
    p = get_object_or_404(Patient, pk=pk)

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
        'age': age,
        'address': address,  # Replace with actual address
        'requests': request_details
    })

@owner_required
def store_testcomponent_session(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        request.session['testcomponent_form_data'] = data
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'}, status=400)

@owner_required
def add_testcomponent(request):
    """
    Display a form to add a new test component.
    """
    show_warning = request.GET.get('show_warning', 'no')
    show_code_warning = request.GET.get('show_code_warning', 'no')

    if request.method == "POST":
        template_name = request.POST.get("template_name")
        
        template = TemplateForm.objects.create(template_name=template_name)

        section_index = 0
        while f"sections[{section_index}][name]" in request.POST:
            section_name = request.POST.get(f"sections[{section_index}][name]")
            section = TemplateSection.objects.create(
                template=template, section_name=section_name
            )

            field_index = 0
            while f"sections[{section_index}][fields][{field_index}][label]" in request.POST:
                label = request.POST.get(f"sections[{section_index}][fields][{field_index}][label]")
                field_type = request.POST.get(f"sections[{section_index}][fields][{field_index}][type]")
                fixed_value = request.POST.get(f"sections[{section_index}][fields][{field_index}][fixed_value]", "")

                TemplateField.objects.create(
                    section=section,
                    label_name=label,
                    field_type=field_type,
                    field_value=fixed_value if fixed_value else None
                )
                field_index += 1
            section_index += 1

    form_data = request.session.get('testcomponent_form_data', {
        'test_code': '',
        'test_name': '',
        'category': '',
        'price': ''
    })

    last_template = TemplateForm.objects.order_by('-template_id').first()
    if TestComponent.objects.filter(template_id=last_template.template_id):
        template_status = 'absent'
    else:
        template_status = 'present'
    return render(request, 'labreqsys/add_testcomponent.html', {
        'template_status': template_status,
        'show_warning': show_warning,
        'show_code_warning': show_code_warning,
        'form_data': form_data})

@owner_required
def view_component(request, component_id):
    test_component = TestComponent.objects.get(component_id=component_id)
    template = test_component.template
    sections = TemplateSection.objects.filter(template=template)

    section_data = []
    for s in sections:
        fields = TemplateField.objects.filter(section_id=s.pk)
        field_count = 0
        for field in fields:
            field_count+=1
        section_data.append({'section': s, 'field_count': field_count, 'fields': fields})
    
    delete_unused_templates()
    request.session.pop('testcomponent_form_data', None)

    return render(request, 'labreqsys/view_component.html',
                  {'component': test_component,
                   'template': template,
                   'sections': section_data
                   })

@owner_required
def create_testcomponent(request):
    """
    Add Test Component to the Database
    """
    
    if request.method == "POST":
        last_template = TemplateForm.objects.order_by('-template_id').first()
        test_code = request.POST.get('test_code')
        if TestComponent.objects.filter(template_id=last_template.template_id):
           request.session['testcomponent_form_data'] = {
               'test_code': request.POST.get('test_code', ''),
               'test_name': request.POST.get('test_name', ''),
               'category': request.POST.get('category', ''),
               'price': request.POST.get('price', '')
               }
           return redirect(f"{reverse('add_testcomponent')}?show_warning=yes")
        elif TestComponent.objects.filter(test_code=test_code):
            request.session['testcomponent_form_data'] = {
               'test_code': request.POST.get('test_code', ''),
               'test_name': request.POST.get('test_name', ''),
               'category': request.POST.get('category', ''),
               'price': request.POST.get('price', '')
               }
            return redirect(f"{reverse('add_testcomponent')}?show_code_warning=yes")
        else:
            test_name = request.POST.get('test_name')
            category = request.POST.get('category')
            component_price = request.POST.get('price')
            TestComponent.objects.create(
                template_id = last_template.template_id,
                test_code = test_code,
                test_name = test_name,
                component_price = component_price,
                category = category
            )
            delete_unused_templates()
            request.session.pop('testcomponent_form_data', None)
    return redirect('testComponents')

@owner_required
def edit_testcomponent(request, component_id):
    test_component = TestComponent.objects.get(component_id=component_id)
    form_data = request.session.get('testcomponent_form_data', {
        'test_code': test_component.test_code,
        'test_name': test_component.test_name,
        'category': test_component.category,
        'price': test_component.component_price,
        })

    return render(request, 'labreqsys/edit_testcomponent.html',
                {'component': test_component,
                'template': test_component.template,
                'form_data': form_data
                })
    
@owner_required
def edit_testcomponent_details(request, component_id):
    if request.method == "POST":
        category = request.POST.get('category')
        component_price = request.POST.get('price')
        TestComponent.objects.filter(component_id=component_id).update(category=category, component_price=component_price)
        delete_unused_templates()
        request.session.pop('testcomponent_form_data', None)
    return redirect('view_component', component_id)
    
@owner_required
def edit_template(request, component_id):
    if request.method == "POST":
        template_name = request.POST.get("template_name")
        
        template = TemplateForm.objects.create(template_name=template_name)

        section_index = 0
        while f"sections[{section_index}][name]" in request.POST:
            section_name = request.POST.get(f"sections[{section_index}][name]")
            section = TemplateSection.objects.create(
                template=template, section_name=section_name
            )

            field_index = 0
            while f"sections[{section_index}][fields][{field_index}][label]" in request.POST:
                label = request.POST.get(f"sections[{section_index}][fields][{field_index}][label]")
                field_type = request.POST.get(f"sections[{section_index}][fields][{field_index}][type]")
                fixed_value = request.POST.get(f"sections[{section_index}][fields][{field_index}][fixed_value]", "")

                TemplateField.objects.create(
                    section=section,
                    label_name=label,
                    field_type=field_type,
                    field_value=fixed_value if fixed_value else None
                )
                field_index += 1
            section_index += 1
        TestComponent.objects.filter(component_id=component_id).update(template=template)

        return redirect ('edit_testcomponent', component_id)
    else:
        component = get_object_or_404(TestComponent, pk=component_id)
        template = component.template

        sections_data = []
        sections = TemplateSection.objects.filter(template=template).order_by('section_id')

        for section in sections:
            fields = TemplateField.objects.filter(section=section).order_by('field_id')
            field_data = []
            for field in fields:
                field_data.append({
                    'label': field.label_name,
                    'type': field.field_type,
                    'fixed_value': field.field_value or ''
                })
            sections_data.append({
                'name': section.section_name,
                'fields': field_data
            })

        template_data = {
            'template_name': template.template_name,
            'sections': sections_data
        }

        context = {
            'component': component,
            'template' : template,
            'initial_template_json': json.dumps(template_data, cls=DjangoJSONEncoder),
        }
        return render(request, 'labreqsys/edit_template.html', context)

@owner_required
def add_template(request):
    """
    Display form builder to create a template.
    """
    editing = 'no'
    return render(request, 'labreqsys/add_template.html', {'editing': editing})

@owner_required
def edit_template_details(request):
    """
    Display form builder for template of a component being made
    """
    template = TemplateForm.objects.order_by('-template_id')[0]

    sections_data = []
    sections = TemplateSection.objects.filter(template=template).order_by('section_id')

    for section in sections:
        fields = TemplateField.objects.filter(section=section).order_by('field_id')
        field_data = []
        for field in fields:
            field_data.append({
                'label': field.label_name,
                'type': field.field_type,
                'fixed_value': field.field_value or ''
            })
        sections_data.append({
            'name': section.section_name,
            'fields': field_data
        })

    template_data = {
        'template_name': template.template_name,
        'sections': sections_data
    }
    editing = 'yes'
    context = {
        'template' : template,
        'initial_template_json': json.dumps(template_data, cls=DjangoJSONEncoder),
        'editing': editing
    }
   
    return render(request, 'labreqsys/add_template.html', context)

@receptionist_or_lab_tech_required
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

@receptionist_or_lab_tech_required
def add_labreq_details(request, pk):
    """
    Handle the selection of components and packages for a new lab request.
    """
    p = get_object_or_404(Patient, pk=pk)
    if request.method == "POST":
        # Safely delete previous lab request items from session
        if 'selected_components' in request.session:
            del request.session['selected_components']
        if 'selected_packages' in request.session:
            del request.session['selected_packages']

        selected_packages = request.POST.getlist('selected_packages')
        selected_components = request.POST.getlist('selected_components')
        request.session['selected_components'] = selected_components
        request.session['selected_packages'] = selected_packages
    return render(request, 'labreqsys/add_labreq_details.html', {'patient': p})

def clear_session(request):
    if 'selected_components' in request.session:
        request.session.pop('selected_components', None)
    if 'selected_packages' in request.session:
        request.session.pop('selected_packages', None)
    return HttpResponse(status=200)  # Return a success response


@receptionist_or_lab_tech_required
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
    discount_type = None
    
    # Apply discount only if patient has a non-empty PWD ID or Senior ID
    has_pwd = p.pwd_id_num and str(p.pwd_id_num).strip()
    has_senior = p.senior_id_num and str(p.senior_id_num).strip()
    if has_pwd or has_senior:
        try:
            discount = round(subtotal * Decimal('0.2'), 2)
            total = subtotal - discount
            discount_type = 'PWD' if has_pwd else 'Senior Citizen'
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
        'discount_type': discount_type,
        'physician': physician,
        'mode_of_release': mode_of_release,
        'request_id': next_request_id
    })

@receptionist_or_lab_tech_required
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

@receptionist_or_lab_tech_required
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
        
        
        
        if lab_request.mode_of_release == 'Both':
            c = CollectionLog.objects.get(request=lab_request, mode_of_collection='Pick-up')
            e = CollectionLog.objects.get(request=lab_request, mode_of_collection='Email')
            
            if c.time_collected and e.time_collected:
                lab_request.overall_status = 'Released'
                lab_request.save()
                
        else:
            lab_request.overall_status = 'Released'
            lab_request.save()
                
    return redirect('view_individual_lab_request', request_id=request_id)

@lab_tech_required
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
    full_name = f"{patient.last_name}, {patient.first_name} {patient.middle_initial} {patient.suffix}"
    
    birthdate = patient.birthdate
    today = date.today()
    
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    
    address_append = []

    if patient.street:
        address_append.append(patient.street)
    if patient.subdivision:
        address_append.append(patient.subdivision)
    if patient.baranggay:
        address_append.append(patient.baranggay)
    if patient.city:
        address_append.append(patient.city)
    if patient.province:
        address_append.append(patient.province)
    if patient.zip_code:
        address_append.append(patient.zip_code)
    
    address = ', '.join(address_append) if address_append else None
    
    if patient.house_num:
        address = f"{patient.house_num} {address}"

    return render(request, 'labreqsys/add_labresult.html', {
        'line_item': line_item,
        'template': template,
        'sections': section_data,
        'patient': patient,
        'request': lab_request,
        'test': test_component,
        'patient_age': age,
        'patient_address': address,
        'lab_technicians': lab_techs
    })

@lab_tech_required
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

@receptionist_required
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
        
        birthdate  = request.POST.get('birthdate')
        birthdate_format = date.fromisoformat(birthdate)
        today = date.today()
        
        age = today.year - birthdate_format.year - ((today.month, today.day) < (birthdate_format.month, birthdate_format.day))
        print(age)
        
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
        
        p_duplicate = []
        if Patient.objects.filter(first_name=first_name, last_name=last_name).exists():
            name_d = {f"Patient {x.patient_id}" for x in Patient.objects.filter(first_name=first_name, last_name=last_name)}
            p_duplicate.append(f"Name: {name_d}")
            
        if email and Patient.objects.filter(email=email):
                email_d = {f"Patient {x.patient_id}" for x in Patient.objects.filter(email=email)}
                p_duplicate.append(f"Email: {email_d}")
        
        if pwd_id_num and Patient.objects.filter(pwd_id_num=pwd_id_num):
                pwd_d = {f"Patient {x.patient_id}" for x in Patient.objects.filter(pwd_id_num=pwd_id_num)}
                p_duplicate.append(f"PWD Number: {pwd_d}")
                
        if senior_id_num and Patient.objects.filter(senior_id_num=senior_id_num):
                senior_d = {f"Patient {x.patient_id}" for x in Patient.objects.filter(senior_id_num=senior_id_num)}
                p_duplicate.append(f"Senior Number: {senior_d}")
        
        if p_duplicate:
            return JsonResponse({'status': 'duplicate', 'p_duplicate':p_duplicate})
        elif age >= 150:
            return JsonResponse({'status': 'ghost'})
        else:
            request.session['new_patient'] = {
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
                'mode': 'add'
            }
            return JsonResponse({'status':'success', 'redirect_url':'/add_patient_details'})   
    else:
        return render(request, 'labreqsys/add_patient.html', {'mode': 'add'})
    


@receptionist_required
def add_patient_details(request):
    '''
    
    Displays preview of Add Patient details, then saves
    
    '''
    
    new_patient = request.session.get('new_patient')
    
    if new_patient: 
        last_name = new_patient['last_name']
        first_name = new_patient['first_name']
        middle_initial = new_patient['middle_initial']
        suffix = new_patient['suffix']
        sex = new_patient['sex']
        civil_status = new_patient['civil_status']
        birthdate = new_patient['birthdate']
        mobile_num = new_patient['mobile_num']
        landline_num = new_patient['landline_num']
        email = new_patient['email']
        house_num = new_patient['house_num']
        street = new_patient['street']
        subdivision = new_patient['subdivision']
        baranggay = new_patient['baranggay']
        province = new_patient['province']
        city = new_patient['city']
        zip_code = new_patient['zip_code']
        pwd_id_num = new_patient['pwd_id_num']
        senior_id_num = new_patient['senior_id_num']
        mode = new_patient['mode']
    else:
        return HttpResponse('There was an error in saving the session. Please refresh your connection.')  
        
    if request.method == "POST":        
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
        request.session.pop('new_patient', None)
        return redirect('view_patient', pk=p.pk)   
    else:
        return render(request, 'labreqsys/add_edit_patient_details.html', {
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
                'mode':mode
                })

@receptionist_required
def edit_patient (request, pk):
    '''
    
    Takes edit patients, then processes for formatting
    
    '''
    
    p = get_object_or_404(Patient, pk=pk)
    
    
    if request.method == "POST":
        last_name = request.POST.get('last_name')
        first_name = request.POST.get('first_name')
        name = last_name + first_name
        
        middle_initial = request.POST.get('middle_initial')
        suffix = request.POST.get('suffix')
        sex = request.POST.get('sex')
        civil_status = request.POST.get('civil_status') 
        
        birthdate  = request.POST.get('birthdate')
        birthdate_format = date.fromisoformat(birthdate)
        today = date.today()
        
        age = today.year - birthdate_format.year - ((today.month, today.day) < (birthdate_format.month, birthdate_format.day))
        print(age)
        
        mobile_num = request.POST.get('mobile_num')
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
        
        p_duplicate = []
        
        p_name = p.last_name + p.first_name
        if name != p_name and Patient.objects.filter(first_name=first_name, last_name=last_name).exists():
            name_d = {f"Patient {x.patient_id}" for x in Patient.objects.filter(first_name=first_name, last_name=last_name)}
            p_duplicate.append(f"Name: {name_d}")
            
        if email and email != p.email and Patient.objects.filter(email=email):
                email_d = {f"Patient {x.patient_id}" for x in Patient.objects.filter(email=email)}
                p_duplicate.append(f"Email: {email_d}")
        
        if pwd_id_num and pwd_id_num != p.pwd_id_num and Patient.objects.filter(pwd_id_num=pwd_id_num):
                pwd_d = {f"Patient {x.patient_id}" for x in Patient.objects.filter(pwd_id_num=pwd_id_num)}
                p_duplicate.append(f"PWD Number: {pwd_d}")
                
        if senior_id_num and senior_id_num != p.senior_id_num and Patient.objects.filter(senior_id_num=senior_id_num):
                senior_d = {f"Patient {x.patient_id}" for x in Patient.objects.filter(senior_id_num=senior_id_num)}
                p_duplicate.append(f"Senior Number: {senior_d}")
        
        if p_duplicate:
            return JsonResponse({'status': 'duplicate', 'p_duplicate':p_duplicate})
        elif age >= 150:
            return JsonResponse({'status': 'ghost'})
        else:
            request.session['edit_patient'] = {
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
                'mode': 'edit'
            }
            redirect_url = reverse('edit_patient_details', args=[p.patient_id])
            return JsonResponse({'status': 'success', 'redirect_url': redirect_url})
        
    else:
        print('NOT POST.')
        return render(request, 'labreqsys/edit_patient.html', {'patient': p, 'mode': 'edit'})

@receptionist_required
def edit_patient_details(request, pk):
    '''
    
    Displays preview of Add Patient details, then saves
    
    ''' 

    patient = get_object_or_404(Patient, pk=pk)
    
    edit_patient = request.session.get('edit_patient')
    
    if edit_patient:
        last_name = edit_patient['last_name']
        first_name = edit_patient['first_name']
        middle_initial = edit_patient['middle_initial']
        suffix = edit_patient['suffix']
        sex = edit_patient['sex']
        civil_status = edit_patient['civil_status']
        birthdate = edit_patient['birthdate']
        mobile_num = edit_patient['mobile_num']
        landline_num = edit_patient['landline_num']
        email = edit_patient['email']
        house_num = edit_patient['house_num']
        street = edit_patient['street']
        subdivision = edit_patient['subdivision']
        baranggay = edit_patient['baranggay']
        province = edit_patient['province']
        city = edit_patient['city']
        zip_code = edit_patient['zip_code']
        pwd_id_num = edit_patient['pwd_id_num']
        senior_id_num = edit_patient['senior_id_num']
        mode = edit_patient['mode']
    
    if request.method == "POST":
        patient.last_name = last_name
        patient.first_name = first_name
        patient.middle_initial = middle_initial
        patient.suffix = suffix
        patient.sex = sex
        patient.civil_status = civil_status
        patient.birthdate = birthdate
        patient.mobile_num = mobile_num
        patient.landline_num = landline_num
        patient.email = email
        patient.house_num = house_num
        patient.street = street
        patient.baranggay = baranggay
        patient.province = province
        patient.city = city
        patient.zip_code = zip_code
        patient.pwd_id_num = pwd_id_num
        patient.senior_id_num = senior_id_num
        patient.save()
        return redirect('view_patient', pk=patient.pk)
    else:
        return render(request, 'labreqsys/add_edit_patient_details.html', {
                'patient':patient,
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
                'mode':mode
                })

@owner_required
def generate_edit_password(request, pk):
    passcode = ''.join(random.choices('0123456789', k=5))
    patient = get_object_or_404(Patient, pk=pk)
    EditPatientPasscode.objects.filter(patient_id=patient).delete()
    EditPatientPasscode.objects.create(patient_id=patient, code=passcode)
    
    return JsonResponse({'pass': passcode})

def password(request, pk):
    if request.method == "POST":
        input_code = request.POST.get('password_input')
        try:
            passcode = EditPatientPasscode.objects.get(patient_id=pk, code=input_code)
        except EditPatientPasscode.DoesNotExist:
            return JsonResponse({"error": "incorrect"})
        
        if timezone.now() > passcode.created_at + timedelta(minutes=5):
            passcode.delete()
            return JsonResponse({"error":"expired"})
        passcode.delete()
        return JsonResponse({"success": 'found', "redirect_url": f"/edit_patient/{pk}"})
        
#@receptionist_or_lab_tech_required
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


    for section in TemplateSection.objects.filter(template=template_form.template_id):
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
        
    address_append = []

    if patient.street:
        address_append.append(patient.street)
    if patient.subdivision:
        address_append.append(patient.subdivision)
    if patient.baranggay:
        address_append.append(patient.baranggay)
    if patient.city:
        address_append.append(patient.city)
    if patient.province:
        address_append.append(patient.province)
    if patient.zip_code:
        address_append.append(patient.zip_code)
    
    address = ', '.join(address_append) if address_append else None
    
    if patient.house_num:
        address = f"{patient.house_num} {address}"


    return render(request, 'labreqsys/pdf.html', 
                {'lab_request': lab_request, 
                'patient': patient, 
                'test_component':test_component,
                'age': age,
                'address': address,
                'template_form': template_form,
                'form' : form,
                'reviewed_by': reviewed_by,
                'lab_tech' : reviews               
                })


@receptionist_or_lab_tech_required
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
    

@receptionist_or_lab_tech_required
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
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response

@lab_tech_required
def view_lab_result(request, pk):
    """
    Display form builder to create a template.
    """
    
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


    for section in TemplateSection.objects.filter(template=template_form.template_id):
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
        
    address_append = []

    if patient.street:
        address_append.append(patient.street)
    if patient.subdivision:
        address_append.append(patient.subdivision)
    if patient.baranggay:
        address_append.append(patient.baranggay)
    if patient.city:
        address_append.append(patient.city)
    if patient.province:
        address_append.append(patient.province)
    if patient.zip_code:
        address_append.append(patient.zip_code)
    
    address = ', '.join(address_append) if address_append else None
    
    if patient.house_num:
        address = f"{patient.house_num} {address}"


    return render(request, 'labreqsys/view_lab_results.html', 
                {'lab_request': lab_request, 
                'patient': patient, 
                'test_component':test_component,
                'age': age,
                'address': address,
                'template_form': template_form,
                'form' : form,
                'reviewed_by': reviewed_by,
                'lab_tech' : reviews,
                'line_item' : line_item              
                })
    
    line_item = get_object_or_404(RequestLineItem, line_item_id=pk)
    return render(request, 'labreqsys/view_lab_results.html', {})


@owner_required
def packages (request):
    '''
    Display packages
    '''
    package = TestPackage.objects.all()
    pc = TestPackageComponent.objects.all()
    
    packages = {}
    for p in package:
        components = TestPackageComponent.objects.filter(package=p)
        packages[p] = components
    
    print (packages)
    return render(request, 'labreqsys/packages.html', {'packages': packages})

@owner_required
def add_package (request):
    '''
    Display packages
    '''
    test_components = TestComponent.objects.all()
    
    tpc = []
    for p in TestPackage.objects.all():
        pc = TestPackageComponent.objects.filter(package=p)
        cmp = []
        for c in pc:
            comp = TestComponent.objects.get(component_id=c.component.component_id).component_id
            cmp.append(f"{comp}")
        tpc.append(cmp)
    
    if request.method == "POST":
        package_name = request.POST.get('package_name')
        price = request.POST.get('price')
        components = request.POST.getlist('addComponentCheckbox')
        
        if TestPackage.objects.filter(package_name=package_name).exists():
            return JsonResponse({'status': 'duplicate1'})
        elif components in tpc:
            return JsonResponse({'status': 'duplicate2'})
        else:
            package = TestPackage.objects.create(package_name=package_name, package_price=price)
            for c in components:
                component = TestComponent.objects.get(component_id=c)
                TestPackageComponent.objects.create(
                    package=package,
                    component=component
                )

        return JsonResponse({'status':'success', 'redirect_url':'/packages'})
    else:
        return render(request, 'labreqsys/add_package.html', {'components': test_components})
    

def edit_package(request, pk):
    '''
    Display packages
    '''    

    package = TestPackage.objects.get(package_id=pk)                  
    all_components = TestComponent.objects.all()  
    pc = TestPackageComponent.objects.filter(package__package_id=pk)                      
    selected_components = []                                                             
    selected_components.extend(                                                          
        TestComponent.objects.get(component_id=p.component.component_id)
        for p in pc 
    )
    
    tpc = []
    for p in TestPackage.objects.all():
        packs = TestPackageComponent.objects.filter(package=p)
        cmp = []
        for c in packs:
            comp = TestComponent.objects.get(component_id=c.component.component_id).component_id
            cmp.append(f"{comp}")
        tpc.append(cmp)
    
    scmp = []
    for s in selected_components:
        scmp.append(str(s.component_id))
    if scmp in tpc:
        tpc.remove(scmp)
    
    if request.method == "POST":
        package_name = request.POST.get('package_name')
        price = request.POST.get('price')
        select = request.POST.getlist('editComponentCheckboxS')
        print(select)
        new = request.POST.getlist('editComponentCheckboxN')
        print(f"edits compons !{new}")
        
        all_comp = select + new
        print (f"yes: {all_comp}")

        updated = []
            
        if package_name != package.package_name and TestPackage.objects.filter(package_name=package_name).exists():
            print ("here1")
            return JsonResponse({'status': 'duplicate1'})
        elif all_comp in tpc:
            print ("here2")
            return JsonResponse({'status': 'duplicate2'})
        else:
            package.package_name = package_name
            package.package_price = price
            package.save()  
            for c in select:
                component = TestComponent.objects.get(component_id=c)
                updated.append(component)
                print(f"huhu: {component}")
        
            for p in selected_components:
                if p not in updated:
                    tp = TestPackageComponent.objects.filter(package=package, component=p)
                    tp.delete()
                        
                
            for x in new:
                component = TestComponent.objects.get(component_id=x)
                TestPackageComponent.objects.create(
                    package=package,
                    component=component
                )
            return JsonResponse({'status':'success', 'redirect_url':'/packages'})
    else:
        return render(request, 'labreqsys/edit_package.html', {
            'components': all_components, 
            'selectedComponents' : selected_components,
            'package':package})

def user_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Lab Tech: enforce signature upload
            if hasattr(user, 'userprofile') and user.userprofile.role == 'lab_tech':
                try:
                    labtech = LabTech.objects.get(user=user)
                    if not labtech.signature_path:
                        return redirect('complete_labtech_profile')
                except LabTech.DoesNotExist:
                    pass
                return redirect('labRequests', requested_status=1)
            elif hasattr(user, 'userprofile') and user.userprofile.role in ['owner', 'receptionist']:
                return redirect('patientList')
            else:
                if getattr(user, 'is_superuser', False):
                    return redirect('patientList')
                return redirect('login')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'labreqsys/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('login')

@owner_required
def register_user(request):
    signature_policy_warning = "Lab Techs will be required to upload their own signature the first time they log in."
    if request.method == 'POST':
        form = UserRegistrationFormWithLabTech(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            role = form.cleaned_data['role']
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'role': role}
            )
            if role == 'lab_tech':
                LabTech.objects.create(
                    user=user,
                    last_name=user.last_name,
                    first_name=user.first_name,
                    title=form.cleaned_data['title'],
                    tech_role=form.cleaned_data['tech_role'],
                    license_num=form.cleaned_data['license_num'],
                    signature_path=''
                )
            # Redirect to success page with username and role
            return redirect(reverse('user_registered_success') + f'?username={user.username}&role={role}')
    else:
        form = UserRegistrationFormWithLabTech()
    return render(request, 'labreqsys/register.html', {'form': form, 'signature_policy_warning': signature_policy_warning})

def user_registered_success(request):
    username = request.GET.get('username')
    role = request.GET.get('role')
    return render(request, 'labreqsys/user_registered_success.html', {'username': username, 'role': role})

@owner_required
def add_testcomponent(request):
    """
    Display a form to add a new test component.
    """
    show_warning = request.GET.get('show_warning', 'no')
    show_code_warning = request.GET.get('show_code_warning', 'no')

    if request.method == "POST":
        template_name = request.POST.get("template_name")
        
        template = TemplateForm.objects.create(template_name=template_name)

        section_index = 0
        while f"sections[{section_index}][name]" in request.POST:
            section_name = request.POST.get(f"sections[{section_index}][name]")
            section = TemplateSection.objects.create(
                template=template, section_name=section_name
            )

            field_index = 0
            while f"sections[{section_index}][fields][{field_index}][label]" in request.POST:
                label = request.POST.get(f"sections[{section_index}][fields][{field_index}][label]")
                field_type = request.POST.get(f"sections[{section_index}][fields][{field_index}][type]")
                fixed_value = request.POST.get(f"sections[{section_index}][fields][{field_index}][fixed_value]", "")

                TemplateField.objects.create(
                    section=section,
                    label_name=label,
                    field_type=field_type,
                    field_value=fixed_value if fixed_value else None
                )
                field_index += 1
            section_index += 1

    form_data = request.session.get('testcomponent_form_data', {
        'test_code': '',
        'test_name': '',
        'category': '',
        'price': ''
    })

    last_template = TemplateForm.objects.order_by('-template_id').first()
    if TestComponent.objects.filter(template_id=last_template.template_id):
        template_status = 'absent'
    else:
        template_status = 'present'
    return render(request, 'labreqsys/add_testcomponent.html', {
        'template_status': template_status,
        'show_warning': show_warning,
        'show_code_warning': show_code_warning,
        'form_data': form_data})

@owner_required
def create_testcomponent(request):
    """
    Add Test Component to the Database
    """
    
    if request.method == "POST":
        last_template = TemplateForm.objects.order_by('-template_id').first()
        test_code = request.POST.get('test_code')
        if TestComponent.objects.filter(template_id=last_template.template_id):
           request.session['testcomponent_form_data'] = {
               'test_code': request.POST.get('test_code', ''),
               'test_name': request.POST.get('test_name', ''),
               'category': request.POST.get('category', ''),
               'price': request.POST.get('price', '')
               }
           return redirect(f"{reverse('add_testcomponent')}?show_warning=yes")
        elif TestComponent.objects.filter(test_code=test_code):
            request.session['testcomponent_form_data'] = {
               'test_code': request.POST.get('test_code', ''),
               'test_name': request.POST.get('test_name', ''),
               'category': request.POST.get('category', ''),
               'price': request.POST.get('price', '')
               }
            return redirect(f"{reverse('add_testcomponent')}?show_code_warning=yes")
        else:
            test_name = request.POST.get('test_name')
            category = request.POST.get('category')
            component_price = request.POST.get('price')
            TestComponent.objects.create(
                template_id = last_template.template_id,
                test_code = test_code,
                test_name = test_name,
                component_price = component_price,
                category = category
            )
            delete_unused_templates()
            request.session.pop('testcomponent_form_data', None)
    return redirect('testComponents')

@owner_required
def add_template(request):
    editing = 'no'
    return render(request, 'labreqsys/add_template.html', {'editing': editing})

@owner_required
def add_lab_tech(request):
    if request.method == 'POST':
        form = LabTechForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                lab_tech = form.save(commit=False)
                signature = form.cleaned_data['signature']
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_name = "".join(c for c in lab_tech.last_name if c.isalnum())
                filename = f"signature_{safe_name}_{timestamp}.png"
                file_path = os.path.join('labreqsys', 'static', 'signatures', filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'wb+') as destination:
                    for chunk in signature.chunks():
                        destination.write(chunk)
                lab_tech.signature_path = f'signatures/{filename}'
                lab_tech.save()
                messages.success(request, 'Lab technician added successfully!')
                return redirect('view_lab_techs')
            except Exception as e:
                messages.error(request, f'Error saving lab technician: {str(e)}')
                if 'file_path' in locals():
                    try:
                        os.remove(file_path)
                    except:
                        pass
    else:
        form = LabTechForm()
    return render(request, 'labreqsys/add_lab_tech.html', {'form': form})

@owner_required
def edit_lab_tech(request, lab_tech_id):
    lab_tech = get_object_or_404(LabTech, pk=lab_tech_id)
    if request.method == 'POST':
        form = EditLabTechForm(request.POST, request.FILES, instance=lab_tech)
        if form.is_valid():
            try:
                lab_tech = form.save(commit=False)
                if 'signature' in request.FILES:
                    signature = request.FILES['signature']
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    safe_name = "".join(c for c in lab_tech.last_name if c.isalnum())
                    filename = f"signature_{safe_name}_{timestamp}.png"
                    file_path = os.path.join('labreqsys', 'static', 'signatures', filename)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    if lab_tech.signature_path:
                        old_path = os.path.join('labreqsys', 'static', lab_tech.signature_path)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    with open(file_path, 'wb+') as destination:
                        for chunk in signature.chunks():
                            destination.write(chunk)
                    lab_tech.signature_path = f'signatures/{filename}'
                lab_tech.save()
                messages.success(request, 'Lab technician updated successfully!')
                return redirect('view_lab_techs')
            except Exception as e:
                messages.error(request, f'Error updating lab technician: {str(e)}')
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

@owner_required
def view_lab_techs(request):
    from django.contrib.auth.models import User
    from .models import UserProfile, LabTech

    staff_profiles = UserProfile.objects.select_related('user').all()
    owners = []
    receptionists = []
    labtechs = []
    labtechs_with_user = set()

    for profile in staff_profiles:
        entry = {
            'user': profile.user,
            'role': profile.role,
            'labtech': None,
            'has_user_account': True,
        }
        if profile.role == 'owner':
            owners.append(entry)
        elif profile.role == 'receptionist':
            receptionists.append(entry)
        elif profile.role == 'lab_tech':
            try:
                labtech = LabTech.objects.get(user=profile.user)
                entry['labtech'] = labtech
                labtechs_with_user.add(labtech.lab_tech_id)
            except LabTech.DoesNotExist:
                entry['labtech'] = None
            labtechs.append(entry)

    # Add LabTechs with no user account
    for labtech in LabTech.objects.filter(user__isnull=True):
        labtechs.append({
            'user': None,
            'role': 'lab_tech',
            'labtech': labtech,
            'has_user_account': False,
        })

    return render(request, 'labreqsys/view_lab_techs.html', {
        'owners': owners,
        'receptionists': receptionists,
        'labtechs': labtechs,
    })

@login_required
def edit_user_profile(request):
    user = request.user
    role = None
    if hasattr(user, 'userprofile'):
        role = user.userprofile.role
    elif user.is_superuser:
        role = 'owner'
    else:
        role = 'receptionist'  # fallback

    profile_form = None
    labtech_form = None
    labtech = None
    labtech_missing_warning = None

    # Receptionist: edit User fields
    if role == 'receptionist' or role == 'owner':
        profile_form = EditReceptionistProfileForm(request.POST or None, instance=user, prefix='profile')
    # Lab Tech: edit User and LabTech fields
    elif role == 'lab_tech':
        try:
            labtech = LabTech.objects.get(user=user)
        except LabTech.DoesNotExist:
            labtech = None
            labtech_missing_warning = "LabTech profile not found for this user. Please contact admin."
        profile_form = EditReceptionistProfileForm(request.POST or None, instance=user, prefix='profile')
        labtech_form = EditLabTechProfileForm(request.POST or None, instance=labtech, prefix='labtech')

    password_form = PasswordChangeForm(user, request.POST or None, prefix='password')

    if request.method == 'POST':
        if 'profile_submit' in request.POST:
            print('DEBUG: Received profile_submit POST')
            valid_profile = profile_form.is_valid() if profile_form else True
            valid_labtech = labtech_form.is_valid() if labtech_form else True
            print(f'DEBUG: valid_profile={valid_profile}, valid_labtech={valid_labtech}')
            if valid_profile and valid_labtech:
                if profile_form:
                    profile_form.save()
                if labtech_form:
                    labtech_form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('edit_user_profile')
            else:
                messages.error(request, 'Please correct the errors below in your profile.')
        elif 'password_submit' in request.POST:
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully.')
                return redirect('edit_user_profile')
            else:
                messages.error(request, 'Please correct the errors below in your password.')

    return render(request, 'labreqsys/edit_user_profile.html', {
        'profile_form': profile_form,
        'labtech_form': labtech_form,
        'password_form': password_form,
        'role': role,
        'user': user,
        'labtech_missing_warning': labtech_missing_warning,
    })

@login_required
def complete_labtech_profile(request):
    user = request.user
    try:
        labtech = LabTech.objects.get(user=user)
    except LabTech.DoesNotExist:
        return redirect('labRequests', requested_status=1)
    error = None

    if request.method == 'POST':
        file = request.FILES.get('signature_path')
        if not file or not file.name.lower().endswith('.png'):
            error = 'Please upload a PNG file.'
        elif file.size > 5 * 1024 * 1024:
            error = 'Signature file size should be less than 5MB.'
        else:
            # Save file to static/signatures/
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = ''.join(c for c in labtech.last_name if c.isalnum())
            filename = f"signature_{safe_name}_{timestamp}.png"
            file_path = os.path.join('labreqsys', 'static', 'signatures', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            labtech.signature_path = f'signatures/{filename}'
            labtech.save()
            # Immediately redirect to dashboard after successful upload
            return redirect('labRequests', requested_status=1)

    return render(request, 'labreqsys/complete_labtech_profile.html', {'error': error, 'labtech': labtech})

@owner_required
def view_users(request):
    from django.contrib.auth.models import User
    users = User.objects.select_related('userprofile').all().order_by('last_name', 'first_name')
    return render(request, 'labreqsys/view_lab_techs.html', {'users': users})
