from django.shortcuts import render, redirect, get_object_or_404
from .models import Propiedad, Reserva
from usuarios.models import PerfilUsuario
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Propiedad, Imagen , Disponibilidad , PropiedadesDeseadas
from django.core.exceptions import PermissionDenied
from .forms import PropiedadForm, ImagenFormSet, FiltroAlojamientosForm, ReservaForm, FiltroAlojamientosHomeForm
from django.forms import ValidationError, modelformset_factory
from decimal import Decimal
from datetime import date
from datetime import datetime
from django.db import transaction
from django.contrib import messages
from django.utils.timezone import now
from django.http import HttpResponseForbidden



def home(request):
    propiedades = Propiedad.objects.all()
    today= now().date()
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
    propiedades_con_disponibilidad = []
    for propiedad in propiedades:
        # Obtener las fechas disponibles de hoy en adelante
        disponibilidad = propiedad.disponibilidades.filter(fecha__gte=today).order_by('fecha')
        propiedades_con_disponibilidad.append({
            'propiedad': propiedad,
            'dias_disponibles': disponibilidad.count()  # Contar los días
        })
    
    return render(request, 'home.html', {'perfil_usuario': perfil_usuario, 'form': form, 'resultados':propiedades_con_disponibilidad})



@login_required
def crear_reserva(request, propiedad_id):
    propiedad = Propiedad.objects.get(pk=propiedad_id)
    fechas_escogidas = request.POST.get("fechas_escogidas", "") 
    fechas_lista = fechas_escogidas.split(",")
    fechas_lista = [fecha.strip() for fecha in fechas_lista]
    
    if request.method == 'POST':
        reserva_form = ReservaForm(request.POST, propiedad_id=propiedad.id)
        
        if reserva_form.is_valid():
            reserva = reserva_form.save(commit=False)
            reserva.inquilino = request.user.perfilusuario  # Asocia la reserva al usuario actual
            reserva.propiedad = propiedad  # Asocia la propiedad seleccionada
            reserva.fechas_reserva = fechas_lista
            reserva.save()  # Guarda la reserva en la base de datos

            return redirect('/')  # Redirige al detalle de la reserva creada
    else:
        reserva_form = ReservaForm(propiedad_id=propiedad.id)  # Pasa el id al formulario


    fechas_disponibles = ", ".join([
            disponibilidad.fecha.strftime("%Y-%m-%d")
            for disponibilidad in Disponibilidad.objects.filter(propiedad=propiedad)
        ])

    return render(request, 'alquileres/crear_reserva.html', {
        'reserva_form': reserva_form,
        'propiedad': propiedad,
        'fechas_disponibles': fechas_disponibles,
        'reserva_form': reserva_form
    })

@login_required
def historial_reservas(request):
    perfil_usuario = request.user.perfilusuario
    reservas = None  # Inicializamos reservas

    # Verificamos el tipo de usuario
    if perfil_usuario.tipo_usuario != "inquilino":  # Cambiado a !=
        # Usamos la relación inversa para obtener las propiedades
        propiedades = Propiedad.objects.filter(propietario=perfil_usuario)
        reservas = Reserva.objects.filter(propiedad__in=propiedades)
    else:
        reservas = Reserva.objects.none()  # Si es inquilino, no hay propiedades asociadas

    return render(request, 'alquileres/historial_reservas.html', {
        'reservas': reservas,
        'perfil_usuario': perfil_usuario,
    })


def buscar_alojamientos(request):
    form = FiltroAlojamientosForm(request.GET or None)  # Formulario para filtros detallados
    query = request.GET.get('query', '')  # Obtener el término de búsqueda desde la barra de búsqueda
    propiedades = Propiedad.objects.all()  # Consulta inicial sin filtros

    today= now().date()


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




    propiedades_con_disponibilidad = []
    for propiedad in propiedades:
        # Obtener las fechas disponibles de hoy en adelante
        disponibilidad = propiedad.disponibilidades.filter(fecha__gte=today).order_by('fecha')
        propiedades_con_disponibilidad.append({
            'propiedad': propiedad,
            'dias_disponibles': disponibilidad.count()  # Contar los días
        })
        

    # Renderizar la plantilla con los resultados de la búsqueda y el formulario de filtros
    return render(request, 'buscar.html', {
        'perfil_usuario': perfil_usuario,
        'form': form,
        'resultados': propiedades_con_disponibilidad,
        'query': query,
    })




@login_required
def crear_propiedad(request):
    if request.method == 'POST':
        propiedad_form = PropiedadForm(request.POST)
        imagen_formset = ImagenFormSet(request.POST, request.FILES)  # Importante pasar request.FILES
        fechas_disponibles = request.POST.get("fechas_disponibles", "")  # Obtener las fechas del formulario

        if propiedad_form.is_valid() and imagen_formset.is_valid():
            try:
                with transaction.atomic():
                    # Crear la propiedad
                    propiedad = propiedad_form.save(commit=False)
                    propiedad.propietario = request.user.perfilusuario
                    propiedad.save()

                    # Asociar imágenes y validar la relación
                    imagen_formset.instance = propiedad
                    imagen_formset.save()
                    if not propiedad.imagenes.exists():
                        raise ValidationError("Cada propiedad debe tener al menos una imagen asociada.")

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

@login_required
def listar_propiedades_propietario(request):
    
    if request.user.is_authenticated:
        perfil_usuario = request.user.perfilusuario  # Solo lo obtenemos si el usuario está autenticado

    else:
        perfil_usuario = None  # Si no está autenticado, no intentamos obtener el perfil
    
    usuario= request.user.perfilusuario.id
    propiedades = Propiedad.objects.all().filter(propietario_id=usuario)

    return render(request, 'alquileres/listar_propiedades.html', {'perfil_usuario': perfil_usuario, 'resultados': propiedades})

@login_required
def eliminar_propiedad(request, propiedad_id):
    propiedad = get_object_or_404(Propiedad, pk=propiedad_id)

    if request.method == "POST":
        propiedad.delete()
        messages.success(request, "El propiedad se eliminó correctamente.")
        return redirect('/gestionPropiedad/') 
    return redirect('/gestionPropiedad/')  

@login_required
def actualizar_propiedad(request, propiedad_id):
    propiedad = get_object_or_404(Propiedad, pk=propiedad_id)

    # Verificar que el usuario sea el propietario
    if propiedad.propietario != request.user.perfilusuario:
        return redirect('/')  # O redirige a una página de error o acceso denegado

    if request.method == 'POST':
        propiedad_form = PropiedadForm(request.POST, instance=propiedad)
        imagen_formset = ImagenFormSet(request.POST, request.FILES, instance=propiedad)
        fechas_disponibles = request.POST.get("fechas_disponibles", "")

        if propiedad_form.is_valid() and imagen_formset.is_valid():
            try:
                with transaction.atomic():
                    # Actualizar la propiedad
                    propiedad = propiedad_form.save(commit=False)
                    propiedad.propietario = request.user.perfilusuario
                    propiedad.save()

                    # Actualizar imágenes
                    imagen_formset.instance = propiedad
                    imagen_formset.save()
                    if not propiedad.imagenes.exists():
                        raise ValidationError("Cada propiedad debe tener al menos una imagen asociada.")

                    # Actualizar fechas disponibles
                    if fechas_disponibles:
                        fechas_list = fechas_disponibles.split(",")
                        # Eliminar fechas anteriores y agregar nuevas
                        Disponibilidad.objects.filter(propiedad=propiedad).delete()
                        for fecha in fechas_list:
                            fecha_obj = datetime.strptime(fecha.strip(), "%Y-%m-%d").date()
                            Disponibilidad.objects.create(propiedad=propiedad, fecha=fecha_obj)

                    # Validar integridad del modelo
                    propiedad.full_clean()

                return redirect('/')  # Redirige a la página de detalle de la propiedad
            except ValidationError as e:
                propiedad_form.add_error(None, e)
    else:
        propiedad_form = PropiedadForm(instance=propiedad)
        imagen_formset = ImagenFormSet(instance=propiedad)
        # Obtener las fechas disponibles existentes como una cadena separada por comas
        fechas_disponibles = ", ".join([
            disponibilidad.fecha.strftime("%Y-%m-%d")
            for disponibilidad in Disponibilidad.objects.filter(propiedad=propiedad)
        ])

    return render(request, 'alquileres/editar_propiedad.html', {
        'propiedad_form': propiedad_form,
        'imagen_formset': imagen_formset,
        'fechas_disponibles': fechas_disponibles,  # Pasar las fechas existentes al template
    })



def mostrar_detalles_propiedad(request, propiedad_id):
    propiedad = get_object_or_404(Propiedad, pk=propiedad_id)
    
    if request.user.is_authenticated:
        perfil_usuario = request.user.perfilusuario  # Solo lo obtenemos si el usuario está autenticado

    else:
        perfil_usuario = None  # Si no está autenticado, no intentamos obtener el perfil

    ya_en_lista_deseos = PropiedadesDeseadas.objects.filter(inquilino=perfil_usuario, propiedad=propiedad).exists()


    fechas_disponibles = ", ".join([
            disponibilidad.fecha.strftime("%Y-%m-%d")
            for disponibilidad in Disponibilidad.objects.filter(propiedad=propiedad)
        ])

    return render(request, 'alquileres/mostrar_propiedad.html', {
        'resultado':propiedad,
        'perfil_usuario': perfil_usuario,
        'fechas_disponibles': fechas_disponibles,
        'ya_en_lista_deseos': ya_en_lista_deseos,

    })


def agregar_propiedad_deseada(request, propiedad_id):
    
    # Obtener el propietario y la propiedad a partir de los ID pasados por URL
    inquilino = get_object_or_404(PerfilUsuario, id=request.user.perfilusuario.id)
    propiedad = get_object_or_404(Propiedad, id=propiedad_id)

    if inquilino.tipo_usuario== "inquilino":
        # Crear el objeto de PropiedadesDeseadas (sin los campos adicionales)
        propiedad_deseada = PropiedadesDeseadas.objects.create()

        # Asociar el propietario y la propiedad a la propiedad deseada
        propiedad_deseada.inquilino.add(inquilino)
        propiedad_deseada.propiedad.add(propiedad)
        return redirect('/')
    
    else:
        # Si el usuario no es inquilino, retornar una respuesta de error
        return HttpResponseForbidden("No tienes permiso para agregar propiedades a la lista de deseos.")


@login_required
def obtener_lista_deseos(request):
    perfil_usuario = request.user.perfilusuario
    reservas = None  # Inicializamos reservas

    # Verificamos el tipo de usuario
    if perfil_usuario.tipo_usuario == "inquilino":  # Cambiado a !=
        # Usamos la relación inversa para obtener las propiedades
        propiedades_deseadas = PropiedadesDeseadas.objects.filter(inquilino=perfil_usuario)
    else:
        propiedades_deseadas = PropiedadesDeseadas.objects.none()  # Si es inquilino, no hay propiedades asociadas

    return render(request, 'alquileres/lista_deseos.html', {
        'propiedades_deseadas': propiedades_deseadas,
        'perfil_usuario': perfil_usuario,
    })



@login_required
def eliminar_de_lista_deseos(request, propiedad_id):
    # Obtén la propiedad que se desea eliminar de la lista de deseos
    propiedad = get_object_or_404(Propiedad, id=propiedad_id)
    
    # Obtén el PerfilUsuario del usuario logueado
    perfil_usuario = request.user.perfilusuario  # Suponiendo que 'perfilusuario' es un campo de relación en 'User'
    
    # Obtén la instancia de PropiedadesDeseadas para el usuario logueado
    # Usamos filter() para obtener todas las listas de deseos asociadas al usuario
    propiedades_deseadas = PropiedadesDeseadas.objects.filter(inquilino=perfil_usuario)
    
    # En este caso, podemos tener varias listas de deseos, pero supongo que un usuario tiene solo una lista activa
    # Eliminamos la propiedad de la lista de deseos
    for lista in propiedades_deseadas:
        lista.propiedad.remove(propiedad)
    
    # Redirige de nuevo a la página de la lista de deseos
    return redirect('/listaDeseos')  # Asegúrate de que esta vista esté bien configurada