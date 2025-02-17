from django.shortcuts import render

def base(request):
    return render(request, 'labreqsys/base.html')

def patientList(request):
    return render(request, 'labreqsys/patientList.html')