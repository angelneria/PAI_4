from django.shortcuts import render, redirect
from .models import Propiedad, Reserva
from usuarios.models import PerfilUsuario
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Propiedad, Imagen  
from django.core.exceptions import PermissionDenied
from .forms import PropiedadForm, ImagenFormSet, FiltroAlojamientosForm
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

def buscar_alojamientos(request):
    form = FiltroAlojamientosForm(request.GET or None)  # Formulario para filtros detallados
    propiedades = Propiedad.objects.all()  # Consulta inicial sin filtros
    print("Datos recibidos:", request.GET)
    # Aplicar filtros del formulario si es válido
    if not form.is_valid():
        print("Errores en el formulario:", form.errors)
    if form.is_valid():
        ubicacion = form.cleaned_data.get('ubicacion')
        precio_min = form.cleaned_data.get('precio_min')
        precio_max = form.cleaned_data.get('precio_max')
        disponible = form.cleaned_data.get('disponible')

        print("Ubicación:", ubicacion)
        print("Precio mínimo:", precio_min)
        print("Precio máximo:", precio_max)
        print("Disponible:", disponible)

        if ubicacion:
            propiedades = propiedades.filter(ubicacion__icontains=ubicacion)
        if precio_min is not None:
            propiedades = propiedades.filter(precio_por_noche__gte=precio_min)
        if precio_max is not None:
            propiedades = propiedades.filter(precio_por_noche__lte=precio_max)
        if disponible is not None:
            if disponible == 'true':
                propiedades = propiedades.filter(disponible=True)
            elif disponible == 'false':
                propiedades = propiedades.filter(disponible=False)


    # Renderizamos la plantilla con el formulario y los resultados
    return render(request, 'buscar.html', {
        'form': form,
        'resultados': propiedades,
    })

def buscar(request):
    query = request.GET.get('query', '')

    if query:
            # Buscar en titulo, descripción y ubicación usando Q para combinar condiciones
            propiedades = Propiedad.objects.filter(
                Q(titulo__icontains=query) |
                Q(descripcion__icontains=query) |
                Q(ubicacion__icontains=query)
            )
    else:
        propiedades = Propiedad.objects.none()

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

            return redirect('/', pk=propiedad.pk)  # Redirige al detalle de la propiedad creada
    else:
        propiedad_form = PropiedadForm()
        imagen_formset = ImagenFormSet()

    return render(request, 'alquileres/crear_propiedad.html', {
        'propiedad_form': propiedad_form,
        'imagen_formset': imagen_formset,
    })

