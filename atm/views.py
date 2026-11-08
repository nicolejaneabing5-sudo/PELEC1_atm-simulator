from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return HttpResponse("Welcome to PELEC1 ATM Simulator")

def pin_entry(request):
    return render(request, 'atm/pin_entry.html')