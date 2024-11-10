from django.shortcuts import render, redirect
from .models import Propiedad, Reserva
from usuarios.models import PerfilUsuario
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Propiedad, Imagen  
from django.core.exceptions import PermissionDenied
from .forms import PropiedadForm, ImagenFormSet
from django.forms import modelformset_factory


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



@login_required
def crear_propiedad(request):
    if request.method == 'POST':
        propiedad_form = PropiedadForm(request.POST)
        imagen_formset = ImagenFormSet(request.POST, request.FILES)  # Importante pasar request.FILES
        
        if propiedad_form.is_valid() and imagen_formset.is_valid():
            propiedad = propiedad_form.save(commit=False)
            propiedad.propietario = request.user.perfilusuario  # Asocia la propiedad al anfitrión
            propiedad.save()  # Guarda la propiedad en la base de datos
            
            # Asocia el formset de imágenes con la propiedad y guarda las imágenes
            imagen_formset.instance = propiedad
            imagen_formset.save()

            return redirect('/', pk=propiedad.pk)  # Redirige al detalle de la propiedad creada
    else:
        propiedad_form = PropiedadForm()
        imagen_formset = ImagenFormSet()

    return render(request, 'alquileres/crear_propiedad.html', {
        'propiedad_form': propiedad_form,
        'imagen_formset': imagen_formset,
    })

