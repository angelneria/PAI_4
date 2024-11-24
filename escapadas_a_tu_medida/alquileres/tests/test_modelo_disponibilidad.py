from django.db import IntegrityError
from django.forms import ValidationError
from django.test import TestCase
from usuarios.models import PerfilUsuario
from django.contrib.auth.models import User
from alquileres.models import Propiedad, Disponibilidad, Imagen
from django.utils.timezone import now, timedelta


class DisponibilidadModelTest(TestCase):
    def test_crear_disponibilidad(self):
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

        Imagen.objects.create(propiedad=propiedad, imagen='escapadas_a_tu_medida/media/navbar.jpg')
        disponibilidad = Disponibilidad.objects.create(fecha=now().date(), propiedad=propiedad)


        self.assertEqual(disponibilidad.propiedad, propiedad)
        self.assertEqual(disponibilidad.fecha, now().date())

    def test_crear_disponibilidad_con_fecha_pasada(self):
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

        Imagen.objects.create(propiedad=propiedad, imagen='escapadas_a_tu_medida/media/navbar.jpg')
        fecha_pasada = now().date() - timedelta(days=1)
        disponibilidad = Disponibilidad.objects.create(fecha=fecha_pasada, propiedad=propiedad)

        with self.assertRaises(ValidationError) as e:
            disponibilidad.full_clean()
        self.assertIn("La fecha de disponibilidad no puede ser anterior a la fecha actual.", str(e.exception))

    def test_unique_together_restriction(self):

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

        Imagen.objects.create(propiedad=propiedad, imagen='escapadas_a_tu_medida/media/navbar.jpg')
        # Crear una disponibilidad inicial
        fecha = now().date() + timedelta(days=1)
        Disponibilidad.objects.create(propiedad=propiedad, fecha=fecha)

        # Intentar crear otra disponibilidad con la misma propiedad y fecha
        with self.assertRaises(IntegrityError) as contexto:
            Disponibilidad.objects.create(propiedad=propiedad, fecha=fecha)

        # Comprobar que el error lanzado se debe a la restricción única
        self.assertIn("UNIQUE constraint failed", str(contexto.exception))


