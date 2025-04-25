from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/patientList', permanent=True)),  # Redirect root URL to /patientList
    path('patientList', views.patientList, name='patientList'),
    path('labRequests', views.labRequests, name='labRequests'),
    path('view_patient/<int:pk>/', views.view_patient, name='view_patient'),
    path('add_labreq/<int:pk>/', views.add_labreq, name = 'add_labreq'),
    path('add_labreq_details/<int:pk>/', views.add_labreq_details, name = 'add_labreq_details'),
    path('summarize_labreq/<int:pk>/', views.summarize_labreq, name = 'summarize_labreq'),
    path('lab_request/<int:request_id>/', views.view_individual_lab_request, name='view_individual_lab_request'),
    path('add_labresult/<int:line_item_id>/', views.add_lab_result, name='add_labresult'),
    path('submit_labresults/<int:line_item_id>/', views.submit_labresults, name='submit_labresults'),
    path('add_patient', views.add_patient, name='add_patient'),
    path('generatePDF', views.generatePDF, name='generatePDF'),
    path('pdf/<int:pk>', views.pdf, name='pdf')

]
#test
