from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.base, name='base'),
    path('patientList', views.patientList, name='patientList'),
    path('view_patient/<int:pk>/', views.view_patient, name='view_patient'),
    path('add_labreq/<int:pk>/', views.add_labreq, name = 'add_labreq'),
    path('summarize_labreq/<int:pk>/', views.summarize_labreq, name = 'summarize_labreq'),
    path('lab_request/<int:request_id>/', views.view_individual_lab_request, name='view_individual_lab_request'),
]