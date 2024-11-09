from django.shortcuts import render, redirect
from .models import Propiedad, Reserva
from usuarios.models import PerfilUsuario
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Propiedad  


def home(request):
    if request.user.is_authenticated:
        perfil_usuario = request.user.perfilusuario  # Solo lo obtenemos si el usuario está autenticado
    else:
        perfil_usuario = None  # Si no está autenticado, no intentamos obtener el perfil
    
    return render(request, 'home.html', {'perfil_usuario': perfil_usuario})

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




def buscar_alojamiento(request):
    query = request.GET.get('query', '')  # Obtener el término de búsqueda desde la URL
    
    if query:
        # Buscar en titulo, descripción y ubicación usando Q para combinar condiciones
        resultados = Propiedad.objects.filter(
            Q(titulo__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(ubicacion__icontains=query)
        )
    else:
        resultados = Propiedad.objects.none()

    return render(request, 'buscar.html', {'resultados': resultados, 'query': query})

