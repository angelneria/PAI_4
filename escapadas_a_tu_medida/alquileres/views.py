from django.shortcuts import render, redirect
from .models import Propiedad, Reserva
from usuarios.models import PerfilUsuario
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Propiedad, Imagen  
from django.core.exceptions import PermissionDenied
from .forms import PropiedadForm, ImagenFormSet, FiltroAlojamientosForm, ReservaForm
from django.forms import modelformset_factory
from decimal import Decimal
from datetime import date

def home(request):
    propiedades = Propiedad.objects.all()
    if request.user.is_authenticated:
        perfil_usuario = request.user.perfilusuario  # Solo lo obtenemos si el usuario está autenticado

    else:
        perfil_usuario = None  # Si no está autenticado, no intentamos obtener el perfil
    
    return render(request, 'home.html', {'perfil_usuario': perfil_usuario, 'resultados':propiedades})



@login_required
def crear_reserva(request, propiedad_id):
    propiedad = Propiedad.objects.get(pk=propiedad_id)
    
    if request.method == 'POST':
        reserva_form = ReservaForm(request.POST)
        
        if reserva_form.is_valid():
            reserva = reserva_form.save(commit=False)
            reserva.inquilino = request.user.perfilusuario  # Asocia la reserva al usuario actual
            reserva.propiedad = propiedad  # Asocia la propiedad seleccionada
            reserva.save()  # Guarda la reserva en la base de datos

            return redirect('/')  # Redirige al detalle de la reserva creada
    else:
        reserva_form = ReservaForm()

    return render(request, 'alquileres/crear_reserva.html', {
        'reserva_form': reserva_form,
        'propiedad': propiedad,
    })


def buscar_alojamientos(request):
    form = FiltroAlojamientosForm(request.GET or None)  # Formulario para filtros detallados
    query = request.GET.get('query', '')  # Obtener el término de búsqueda desde la barra de búsqueda
    
    # Realizar la búsqueda inicial con el query si está presente
    propiedades = Propiedad.objects.all()
    
    if query:
        propiedades = propiedades.filter(
            Q(titulo__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(ubicacion__icontains=query)
        )

    # Aplicar filtros del formulario si es válido
    if form.is_valid():
        ubicacion = form.cleaned_data.get('ubicacion')
        precio_min = form.cleaned_data.get('precio_min')
        precio_max = form.cleaned_data.get('precio_max')

        # Filtro por ubicación
        if ubicacion:
            propiedades = propiedades.filter(ubicacion__icontains=ubicacion)
        
        # Filtro por precio mínimo
        if precio_min is not None:
            propiedades = propiedades.filter(precio_por_noche__gte=precio_min)
        
        # Filtro por precio máximo
        if precio_max is not None:
            propiedades = propiedades.filter(precio_por_noche__lte=precio_max)
        

    # Renderizar la plantilla con los resultados de la búsqueda y el formulario de filtros
    return render(request, 'buscar.html', {
        'form': form,
        'resultados': propiedades,
        'query': query,
    })



def buscar(request):
    query = request.GET.get('query', '')
    propiedades = Propiedad.objects.none()  # Inicializar siempre


    if query:
        # Buscar propiedades
        propiedades = Propiedad.objects.filter(
            Q(titulo__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(ubicacion__icontains=query)
        )

        # Serializar resultados
        resultados = []
        for propiedad in propiedades:
            resultados.append({
                'id': propiedad.id,
                'titulo': propiedad.titulo,
                'ubicacion': propiedad.ubicacion,
                'precio_por_noche': float(propiedad.precio_por_noche),  # Decimal a float
            })

        # Guardar en la sesión
        request.session['resultados'] = resultados
    else:
        request.session['resultados'] = []

    return render(request, 'buscar.html', {'resultados': propiedades, 'query': query})





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

            return redirect('/')  # Redirige al detalle de la propiedad creada
    else:
        propiedad_form = PropiedadForm()
        imagen_formset = ImagenFormSet()

    return render(request, 'alquileres/crear_propiedad.html', {
        'propiedad_form': propiedad_form,
        'imagen_formset': imagen_formset,
    })

