'''from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return HttpResponse("Welcome to PELEC1 ATM Simulator")'''

from django.shortcuts import render

def pin_entry_view(request):
    return render(request, 'atm/pin_entry.html')

def dashboard_view(request):
    return render(request, 'atm/dashboard.html')