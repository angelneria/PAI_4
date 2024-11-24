from django.db import IntegrityError
from django.forms import ValidationError
from django.test import TestCase
from usuarios.models import PerfilUsuario
from django.contrib.auth.models import User
from alquileres.models import Propiedad, Disponibilidad, Imagen
from django.utils.timezone import now, timedelta


class ImagenModelTest(TestCase):
    def test_crear_imagen(self):
        propietario = PerfilUsuario.objects.create(
            usuario= User.objects.create_user(username='testuser', password='testpassword'),
            tipo_usuario='anfitrion',
            telefono='1234567890'
        )

        propiedad = Propiedad.objects.create(
            propietario=propietario,
            titulo='Test Propiedad',
            descripcion='Test Descripcion',
            ubicacion='Test Ubicacion',
            precio_por_noche=100.00,
            num_maximo_huespedes=2,
            num_maximo_habitaciones=1,
            servicios_disponibles='Test Servicios'
        )

        imagen =Imagen.objects.create(propiedad=propiedad, imagen='escapadas_a_tu_medida/media/navbar.jpg')
        disponibilidad = Disponibilidad.objects.create(fecha=now().date(), propiedad=propiedad)


        self.assertEqual(imagen.propiedad, propiedad)
        self.assertEqual(imagen.imagen.name, 'escapadas_a_tu_medida/media/navbar.jpg')