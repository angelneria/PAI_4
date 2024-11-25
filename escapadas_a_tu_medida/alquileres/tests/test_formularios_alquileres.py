from django.test import TestCase
from alquileres.models import Propiedad
from usuarios.models import PerfilUsuario
from alquileres.forms import (
    ImagenFormSet,
    PropiedadForm,
    FiltroAlojamientosForm,
    ReservaForm,
)
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile


class ImagenFormSetTest(TestCase):
    def setUp(self):

        self.user = get_user_model().objects.create_user(username='usuario', password='testpassword')

        self.perfil_usuario = PerfilUsuario.objects.create(
            usuario=self.user,
            tipo_usuario="anfitrion"
        )


        self.propiedad = Propiedad.objects.create(
            titulo="Casa en la playa",
            descripcion="Hermosa casa junto al mar",
            ubicacion="Playa de Palma",
            precio_por_noche=100.00,
            num_maximo_huespedes=6,
            num_maximo_habitaciones=3,
            propietario=self.perfil_usuario,
            tipo = 'apartamento',
            servicios_disponibles='Wifi, Piscina'
        )

    def test_formset_valid(self):
        # Crear un archivo de imagen válido (simulado)
        uploaded_file = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF\x21\xF9\x04\x00\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4C\x01\x00\x3B',
            content_type='image/jpeg'
        )

        # Ajustar los nombres de los campos según el prefijo esperado
        data = {
            'imagenes-TOTAL_FORMS': '1',
            'imagenes-INITIAL_FORMS': '0',
            'imagenes-MIN_NUM_FORMS': '0',
            'imagenes-MAX_NUM_FORMS': '10',
        }

        files = {
            'imagenes-0-imagen': uploaded_file,
        }

        # Crear el FormSet con los datos ajustados
        formset = ImagenFormSet(data, files, instance=self.propiedad)

        # Imprimir errores para depuración si el FormSet no es válido
        if not formset.is_valid():
            print("Errores del FormSet:", formset.errors)
            print("Errores generales:", formset.non_form_errors())

        # Asegurar que el FormSet es válido
        self.assertTrue(formset.is_valid())


    def test_formset_exceeds_max(self):
        data = {
            'imagen_set-TOTAL_FORMS': '11',
            'imagen_set-INITIAL_FORMS': '0',
        }
        formset = ImagenFormSet(data, instance=self.propiedad)
        self.assertFalse(formset.is_valid())


class PropiedadFormTest(TestCase):
    def test_form_valid(self):
        propiedad_data = {
            'titulo': 'Casa en el bosque',
            'descripcion': 'Una casa tranquila en el bosque',
            'ubicacion': 'Bosque de los Álamos',
            'precio_por_noche': 120.00,
            'num_maximo_huespedes': 4,
            'num_maximo_habitaciones': 2,
            'servicios_disponibles': 'Calefacción, Wifi',
            'tipo': 'casa',
            'fechas_disponibles': '2024-12-01, 2024-12-02',
        }
        form = PropiedadForm(propiedad_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        data = {
            'titulo': '',
            'descripcion': '',
            'ubicacion': '',
            'precio_por_noche': '12',
            'num_maximo_huespedes': '',
            'num_maximo_habitaciones': '',
            'servicios_disponibles': '',
            'tipo': '',        
            }
        form = PropiedadForm(data)
        self.assertFalse(form.is_valid())


class FiltroAlojamientosFormTest(TestCase):
    def test_form_valid(self):
        data = {
            'query': 'Playa',
            'precio_min': '50.00',
            'precio_max': '200.00',
        }
        form = FiltroAlojamientosForm(data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_price_range(self):
        data = {
            'precio_min': '300.00',
            'precio_max': '200.00',  # Precio mínimo mayor al máximo
        }
        form = FiltroAlojamientosForm(data)
        self.assertFalse(form.is_valid())


class ReservaFormTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='usuario', password='testpassword')

        self.perfil_usuario = PerfilUsuario.objects.create(
            usuario=self.user,
            tipo_usuario="anfitrion"
        )


        self.propiedad = Propiedad.objects.create(
            titulo="Casa en la playa",
            descripcion="Hermosa casa junto al mar",
            ubicacion="Playa de Palma",
            precio_por_noche=100.00,
            num_maximo_huespedes=6,
            num_maximo_habitaciones=3,
            propietario=self.perfil_usuario,
            tipo = 'apartamento',
            servicios_disponibles='Wifi, Piscina'
        )

    def test_form_valid(self):
        data = {
            'numero_huespedes': 3,
            'nombre_usuario_anonimo': 'John Doe',
            'correo_usuario_anonimo': 'johndoe@example.com',
            'telefono_usuario_anonimo': '1234567890',
        }
        form = ReservaForm(data, propiedad_id=self.propiedad.id)
        self.assertTrue(form.is_valid())

    def test_form_exceeds_max_guests(self):
        data = {
            'numero_huespedes': 6,  # Excede el máximo
        }
        form = ReservaForm(data, propiedad_id=self.propiedad.id)
        self.assertFalse(form.is_valid())
