from django.shortcuts import render

# alquileres/views.py
from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

