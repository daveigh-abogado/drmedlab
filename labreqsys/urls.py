from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.base, name='base'),
    path('patientList', views.patientList, name='patientList'),
    path('view_patient/<int:pk>/', views.view_patient, name='view_patient')
]