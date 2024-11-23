from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
import stripe
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
from django.http import HttpResponseForbidden, JsonResponse
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse



def home(request):
    propiedades = Propiedad.objects.all()
    today= now().date()
    if request.user.is_authenticated:
        perfil_usuario = request.user.perfilusuario  # Solo lo obtenemos si el usuario está autenticado

    else:
        perfil_usuario = None  # Si no está autenticado, no intentamos obtener el perfil
    
    form = FiltroAlojamientosHomeForm(request.GET)  # Formulario para filtros detallados
    if form.is_valid():
        ubicacion = form.cleaned_data.get('ubicacion')
        precio_min = form.cleaned_data.get('precio_min')
        precio_max = form.cleaned_data.get('precio_max')
        num_maximo_huespedes = form.cleaned_data.get('num_maximo_huespedes')
        num_maximo_habitaciones = form.cleaned_data.get('num_maximo_habitaciones')


        # Filtro por ubicación
        if ubicacion:
            propiedades = propiedades.filter(ubicacion__icontains=ubicacion)
        
        # Filtro por num_maximo_huespedes
        if num_maximo_huespedes is not None:
            propiedades = propiedades.filter(num_maximo_huespedes__gte=num_maximo_huespedes)
            propiedades = propiedades.order_by('num_maximo_huespedes')
        
        # Filtro por num_maximo_habitaciones
        if num_maximo_habitaciones is not None:
            propiedades = propiedades.filter(num_maximo_habitaciones=num_maximo_habitaciones)

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




def crear_reserva(request, propiedad_id):
    propiedad = Propiedad.objects.get(pk=propiedad_id)
    fechas_escogidas = request.POST.get("fechas_escogidas", "")
    numero_huespedes = request.POST.get("numero_huespedes", "")
    fechas_lista = fechas_escogidas.split(",")
    fechas_lista = [fecha.strip() for fecha in fechas_lista]
    user_authenticated = request.user.is_authenticated


    if request.method == 'POST':

        reserva_form = ReservaForm(request.POST, propiedad_id=propiedad.id, user_authenticated=user_authenticated)


        if reserva_form.is_valid():
            # Datos para usuarios no registrados
            nombre_cliente = reserva_form.cleaned_data.get('nombre_usuario_anonimo')
            email_cliente = reserva_form.cleaned_data.get('correo_usuario_anonimo')
            telefono_cliente = reserva_form.cleaned_data.get('telefono_usuario_anonimo')

            # Datos para la reserva
            numero_huespedes = reserva_form.cleaned_data.get('numero_huespedes')
            fechas_lista = request.POST.get("fechas_escogidas", "").split(",")
            fechas_lista = [fecha.strip() for fecha in fechas_lista]

            # Cálculo del monto
            monto = calcular_monto(fechas_lista, propiedad)

            # Almacena los datos en la sesión
            request.session['fechas_reserva'] = fechas_lista
            request.session['numero_huespedes'] = numero_huespedes
            request.session['nombre_cliente'] = nombre_cliente
            request.session['email_cliente'] = email_cliente
            request.session['telefono_cliente'] = telefono_cliente
            request.session['monto'] = monto

            # Redirigir a procesar pago
            return redirect('procesar_pago', propiedad_id=propiedad.id, monto=monto)

    else:
        reserva_form = ReservaForm(propiedad_id=propiedad.id)

    fechas_disponibles = ", ".join([disponibilidad.fecha.strftime("%Y-%m-%d")
                                    for disponibilidad in Disponibilidad.objects.filter(propiedad=propiedad)
                                   ])

    return render(request, 'alquileres/crear_reserva.html', {
        'reserva_form': reserva_form,
        'propiedad': propiedad,
        'fechas_disponibles': fechas_disponibles,
        'user_authenticated': request.user.is_authenticated ,
    })



def calcular_monto(fechas_lista, propiedad):
    # Aquí puedes calcular el monto en función de las fechas seleccionadas y la propiedad
    # Este es solo un ejemplo; ajusta según tu lógica
    monto = len(fechas_lista) * propiedad.precio_por_noche
    return str(monto)


def enviar_correo(asunto, destinatario, nombre_destinatario, propiedad_reservada, reserva, request):
    asunto = asunto
    destinatario = destinatario
    url_seguimiento = request.build_absolute_uri(
        reverse("seguir_reservas", kwargs={"reserva_id": reserva.id})
    )
    # Renderizar contenido HTML
    mensaje_html = render_to_string("alquileres/correo_reserva.html", {"usuario": str(nombre_destinatario), "propiedad": propiedad_reservada, "reserva":reserva, "url_seguimiento": url_seguimiento})

    email = EmailMessage(
        asunto,
        mensaje_html,
        settings.EMAIL_HOST_USER,  # Remitente
        [destinatario],  # Destinatarios
    )
    email.content_subtype = "html"  # Indicar que el mensaje es HTML

    email.send(fail_silently=False)

    




def confirmar_reserva(request, propiedad_id):
    propiedad = Propiedad.objects.get(pk=propiedad_id)

    # Recupera las fechas de la sesión
    fechas_lista = request.session.get('fechas_reserva', [])
    numero_huespedes = request.session.get('numero_huespedes', None)
    nombre_cliente = request.session.get('nombre_cliente', None)
    email_cliente = request.session.get('email_cliente', None)
    telefono_cliente = request.session.get('telefono_cliente', None)
    monto = request.session.get('monto', None)

        # Crea el PaymentIntent en Stripe
    monto = float(monto)  # Convierte el monto a un valor flotante
    monto = int(monto * 100)
    
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=monto,  # El monto debe estar en centavos (por ejemplo, $10 sería 1000)
            currency="eur",  # O la moneda que desees usar
            metadata={
                'propiedad_id': propiedad_id,
                'user_id': request.user.id,
            },
        )
    except stripe.error.StripeError as e:
        return JsonResponse({'error': str(e)})

    if request.user.is_authenticated:
        # Si el usuario está autenticado, usamos su perfil
        inquilino = request.user.perfilusuario
        destinatario = inquilino.usuario.email
        nombre_destinatario = inquilino.usuario.username
    else:
        # Si el usuario no está autenticado, usamos "Anonymous" o los datos del formulario
        inquilino = None    # Puede ser None o una referencia a un "perfil anónimo"
        destinatario = email_cliente
        nombre_destinatario = nombre_cliente  

    # Aquí ya no es necesario el formulario, creamos la reserva directamente
    reserva = Reserva(
        inquilino=inquilino,  # Asocia la reserva al usuario actual
        propiedad=propiedad,  # Asocia la propiedad seleccionada
        fechas_reserva=fechas_lista,  # Usa las fechas recuperadas de la sesión
        numero_huespedes = numero_huespedes,
        nombre_usuario_anonimo = nombre_cliente,
        correo_usuario_anonimo = email_cliente,
        telefono_usuario_anonimo = telefono_cliente,
    )
    reserva.save()  # Guarda la reserva en la base de datos



    asunto = "Confirmación de reserva"
    propiedad_reservada = reserva.propiedad
    enviar_correo(asunto, destinatario, nombre_destinatario, propiedad_reservada, reserva, request)

    return JsonResponse({'clientSecret': payment_intent.client_secret})


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



def pago_realizado(request):
    return render(request, 'alquileres/confirmar_reserva.html')



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
        # Obtener los valores de los campos del formulario
        ubicacion = form.cleaned_data.get('ubicacion')
        precio_min = form.cleaned_data.get('precio_min')
        precio_max = form.cleaned_data.get('precio_max')
        num_maximo_huespedes = form.cleaned_data.get('num_maximo_huespedes')
        num_maximo_habitaciones = form.cleaned_data.get('num_maximo_habitaciones')


        # Filtro por ubicación
        if ubicacion:
            propiedades = propiedades.filter(ubicacion__icontains=ubicacion)
        
        # Filtro por num_maximo_huespedes
        if num_maximo_huespedes is not None:
            propiedades = propiedades.filter(num_maximo_huespedes__gte=num_maximo_huespedes)
            propiedades = propiedades.order_by('-num_maximo_huespedes')
        
        # Filtro por num_maximo_habitaciones
        if num_maximo_habitaciones is not None:
            propiedades = propiedades.filter(num_maximo_habitaciones=num_maximo_habitaciones)

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
        fechas_disponibles = request.POST.get("fechas_disponibles", "")  # Obtener las fechas del formulario
        imagenes = request.FILES.getlist('imagenes')  # Obtener múltiples imágenes del campo de entrada

        # Inicializar el formset vacío por si falla la validación del formulario principal
        imagen_formset = ImagenFormSet(request.POST, request.FILES)

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
            # Aquí manejamos el caso en que el formulario no es válido
            imagen_formset = ImagenFormSet()  # Reasignar por coherencia en el flujo

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
    propiedad = get_object_or_404(Propiedad, id=propiedad_id, propietario=request.user.perfilusuario)

    if request.method == 'POST':
        propiedad_form = PropiedadForm(request.POST, instance=propiedad)
        imagenes = request.FILES.getlist('imagenes')
        fechas_disponibles = request.POST.get("fechas_disponibles", "")

        if propiedad_form.is_valid():
            try:
                with transaction.atomic():
                    # Guardar la propiedad
                    propiedad = propiedad_form.save(commit=False)
                    propiedad.save()

                    # Manejar imágenes
                    if len(imagenes) > 10:
                        raise ValidationError("No puedes subir más de 10 imágenes.")

                    # Eliminar imágenes seleccionadas para eliminar
                    imagenes_a_eliminar = request.POST.getlist('eliminar_imagenes')
                    Imagen.objects.filter(id__in=imagenes_a_eliminar, propiedad=propiedad).delete()

                    # Guardar nuevas imágenes
                    for imagen in imagenes:
                        Imagen.objects.create(propiedad=propiedad, imagen=imagen)

                    # Actualizar fechas disponibles
                    nuevas_fechas = set()
                    if fechas_disponibles:
                        fechas_list = fechas_disponibles.split(",")
                        nuevas_fechas = {
                            datetime.strptime(fecha.strip(), "%Y-%m-%d").date() for fecha in fechas_list
                        }

                    # Fechas ya guardadas en la base de datos
                    fechas_actuales = set(
                        Disponibilidad.objects.filter(propiedad=propiedad).values_list('fecha', flat=True)
                    )

                    # Eliminar fechas desmarcadas
                    fechas_a_eliminar = fechas_actuales - nuevas_fechas
                    Disponibilidad.objects.filter(propiedad=propiedad, fecha__in=fechas_a_eliminar).delete()

                    # Agregar nuevas fechas
                    fechas_a_agregar = nuevas_fechas - fechas_actuales
                    for fecha in fechas_a_agregar:
                        Disponibilidad.objects.create(propiedad=propiedad, fecha=fecha)

                    # Validar cambios
                    propiedad.full_clean()

                return redirect('/')  # Redirige tras guardar los cambios
            except ValidationError as e:
                propiedad_form.add_error(None, e)

    else:
        propiedad_form = PropiedadForm(instance=propiedad)

    # Obtener TODAS las fechas disponibles para esta propiedad
    fechas_disponibles = ",".join(
        [d.fecha.strftime("%Y-%m-%d") for d in Disponibilidad.objects.filter(propiedad=propiedad)]
    )

    # Obtener imágenes actuales de la propiedad
    imagenes_actuales = Imagen.objects.filter(propiedad=propiedad)

    return render(request, 'alquileres/editar_propiedad.html', {
        'propiedad_form': propiedad_form,
        'fechas_disponibles': fechas_disponibles,
        'imagenes_actuales': imagenes_actuales,  # Pasar imágenes actuales al template
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

def seguir_reservas(request, reserva_id):
    # Obtener la reserva específica por su ID
    reserva = get_object_or_404(Reserva, id=reserva_id)

    # Pasar los detalles de la reserva al template
    return render(request, 'alquileres/seguimiento_reserva.html', {
        'reserva': reserva,
    })