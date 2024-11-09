from django.shortcuts import render, redirect
from .models import Propiedad, Reserva
from usuarios.models import PerfilUsuario
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request, 'home.html')

@login_required
def listar_propiedades(request):
    if request.user.perfilusuario.es_anfitrion():
        propiedades = Propiedad.objects.filter(propietario=request.user.perfilusuario)
    else:
        propiedades = Propiedad.objects.filter(disponible=True)
    return render(request, 'alquileres/listar_propiedades.html', {'propiedades': propiedades})

@login_required
def reservar_propiedad(request, propiedad_id):
    propiedad = Propiedad.objects.get(id=propiedad_id)
    if request.user.perfilusuario.es_inquilino():
        # lógica para reservar la propiedad
        pass
    return redirect('listar_propiedades')
