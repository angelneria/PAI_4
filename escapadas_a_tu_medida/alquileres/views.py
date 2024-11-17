from django.shortcuts import render, redirect
from .models import Propiedad, Reserva
from usuarios.models import PerfilUsuario
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Propiedad, Imagen , Disponibilidad 
from django.core.exceptions import PermissionDenied
from .forms import PropiedadForm, ImagenFormSet, FiltroAlojamientosForm, ReservaForm, FiltroAlojamientosHomeForm
from django.forms import ValidationError, modelformset_factory
from decimal import Decimal
from datetime import date
from datetime import datetime
from django.db import transaction


def home(request):
    propiedades = Propiedad.objects.all()
    if request.user.is_authenticated:
        perfil_usuario = request.user.perfilusuario  # Solo lo obtenemos si el usuario está autenticado

    else:
        perfil_usuario = None  # Si no está autenticado, no intentamos obtener el perfil
    
    form = FiltroAlojamientosHomeForm(request.GET)  # Formulario para filtros detallados
    if form.is_valid():
        precio_min = form.cleaned_data.get('precio_min')
        precio_max = form.cleaned_data.get('precio_max')
        
        # Filtro por precio mínimo
        if precio_min is not None:
            propiedades = propiedades.filter(precio_por_noche__gte=precio_min)
        
        # Filtro por precio máximo
        if precio_max is not None:
            propiedades = propiedades.filter(precio_por_noche__lte=precio_max)
        

    
    return render(request, 'home.html', {'perfil_usuario': perfil_usuario, 'form': form, 'resultados':propiedades})



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
    propiedades = Propiedad.objects.all()  # Consulta inicial sin filtros

    if request.user.is_authenticated:
        perfil_usuario = request.user.perfilusuario  # Solo lo obtenemos si el usuario está autenticado

    else:
        perfil_usuario = None  # Si no está autenticado, no intentamos obtener el perfil
    
    # Realizar la búsqueda inicial con el query si está presente    
    if query:
        propiedades = propiedades.filter(
            Q(titulo__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(ubicacion__icontains=query)
        )

    # Aplicar filtros del formulario si es válido
    if form.is_valid():
        precio_min = form.cleaned_data.get('precio_min')
        precio_max = form.cleaned_data.get('precio_max')
        
        # Filtro por precio mínimo
        if precio_min is not None:
            propiedades = propiedades.filter(precio_por_noche__gte=precio_min)
        
        # Filtro por precio máximo
        if precio_max is not None:
            propiedades = propiedades.filter(precio_por_noche__lte=precio_max)
        

    # Renderizar la plantilla con los resultados de la búsqueda y el formulario de filtros
    return render(request, 'buscar.html', {
        'perfil_usuario': perfil_usuario,
        'form': form,
        'resultados': propiedades,
        'query': query,
    })




@login_required
def crear_propiedad(request):
    if request.method == 'POST':
        propiedad_form = PropiedadForm(request.POST)
        # imagen_formset = ImagenFormSet(request.POST, request.FILES)  # Importante pasar request.FILES
        fechas_disponibles = request.POST.get("fechas_disponibles", "")  # Obtener las fechas del formulario

        imagenes = request.FILES.getlist('imagenes')  # Obtener múltiples imágenes del campo de entrada

        if propiedad_form.is_valid():
            try:
                with transaction.atomic():
                    # Guardar la propiedad
                    propiedad = propiedad_form.save(commit=False)
                    propiedad.propietario = request.user.perfilusuario
                    propiedad.save()

                    # Guardar las imágenes
                    if len(imagenes) > 10:
                        raise ValidationError("No puedes subir más de 10 imágenes.")

                    for imagen in imagenes:
                        Imagen.objects.create(propiedad=propiedad, imagen=imagen)

                    # Guardar fechas disponibles
                    if fechas_disponibles:
                        fechas_list = fechas_disponibles.split(",")  # Las fechas están separadas por comas
                        for fecha in fechas_list:
                            fecha_obj = datetime.strptime(fecha.strip(), "%Y-%m-%d").date()  # Convierte la fecha en objeto date
                            Disponibilidad.objects.create(propiedad=propiedad, fecha=fecha_obj)

                    # Validar fechas disponibles en el modelo
                    propiedad.full_clean()

                return redirect('/')  # Redirige al detalle de la propiedad creada
            except ValidationError as e:
                propiedad_form.add_error(None, e)

    else:
        propiedad_form = PropiedadForm()
        imagen_formset = ImagenFormSet()

    return render(request, 'alquileres/crear_propiedad.html', {
        'propiedad_form': propiedad_form,
        'imagen_formset': imagen_formset,
    })