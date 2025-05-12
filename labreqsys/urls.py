from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/patientList', permanent=True)),  # Redirect root URL to /patientList
    path('patientList', views.patientList, name='patientList'),
    path('labRequests/<int:requested_status>/', views.labRequests, name='labRequests'),
    path('testComponents', views.testComponents, name='testComponents'),
    path('add_testcomponent', views.add_testcomponent, name='add_testcomponent'),
    path('edit_testcomponent/<int:component_id>', views.edit_testcomponent, name='edit_testcomponent'),
    path('edit_testcomponent_details/<int:component_id>', views.edit_testcomponent_details, name='edit_testcomponent_details'),
    path('store_testcomponent_session/', views.store_testcomponent_session, name='store_testcomponent_session'),
    path('create_testcomponent', views.create_testcomponent, name='create_testcomponent'),
    path('view_component/<int:component_id>/', views.view_component, name='view_component'),
    path('add_template', views.add_template, name='add_template'),
    path('edit_template_details', views.edit_template_details, name='edit_template_details'),
    path('edit_template/<int:component_id>', views.edit_template, name='edit_template'),
    path('view_patient/<int:pk>/', views.view_patient, name='view_patient'),
    path('add_labreq/<int:pk>/', views.add_labreq, name = 'add_labreq'),
    path('add_labreq_details/<int:pk>/', views.add_labreq_details, name = 'add_labreq_details'),
    path('summarize_labreq/<int:pk>/', views.summarize_labreq, name = 'summarize_labreq'),
    path('lab_request/<int:request_id>/', views.view_individual_lab_request, name='view_individual_lab_request'),
    path('add_labresult/<int:line_item_id>/', views.add_lab_result, name='add_labresult'),
    path('submit_labresults/<int:line_item_id>/', views.submit_labresults, name='submit_labresults'),
    path('add_patient', views.add_patient, name='add_patient'),
    path('edit_patient/<int:pk>', views.edit_patient, name='edit_patient'),
    path('add_patient_details', views.add_patient_details, name='add_patient_details'),
    path('edit_patient_details/<int:pk>', views.edit_patient_details, name='edit_patient_details'),
    path('generatePDF', views.generatePDF, name='generatePDF'),
    path('pdf/<int:pk>', views.pdf, name='pdf'),
    path('add_lab_tech/', views.add_lab_tech, name='add_lab_tech'),
    path('lab_techs/', views.view_lab_techs, name='view_lab_techs'),
    path('edit_lab_tech/<int:lab_tech_id>/', views.edit_lab_tech, name='edit_lab_tech'),
    path('view_labresult/<int:pk>', views.view_lab_result, name='view_labresult'),
    path('save_patient', views.save_patient, name='save_patient'),
    path('packages', views.packages, name='packages'),
    path('add_package', views.add_package, name='add_package'),
    path('change_collection_status/<int:request_id>', views.change_collection_status, name='change_collection_status'),
    path('edit_package/<int:pk>', views.edit_package, name='edit_package'),
    path('register/', views.register_user, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
]

