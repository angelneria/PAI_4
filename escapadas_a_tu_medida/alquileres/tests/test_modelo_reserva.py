from datetime import date
from django.db import IntegrityError
from django.forms import ValidationError
from django.test import TestCase
from usuarios.models import PerfilUsuario
from django.contrib.auth.models import User
from alquileres.models import Propiedad, Disponibilidad, Imagen, Reserva
from django.utils.timezone import now, timedelta


class ReservaModelTest(TestCase):
    def setUp(self):
        # Crear un usuario de tipo inquilino
        self.usuario = User.objects.create_user(
            username="inquilino1",
            password="password123"
        )
        self.perfil_usuario = PerfilUsuario.objects.create(
            usuario=self.usuario,
            tipo_usuario="inquilino"
        )

        # Crear una propiedad
        self.propiedad = Propiedad.objects.create(
            propietario=self.perfil_usuario,
            titulo='Test Propiedad',
            descripcion='Test Descripcion',
            ubicacion='Test Ubicacion',
            precio_por_noche=100.00,
            num_maximo_huespedes=2,
            num_maximo_habitaciones=1,
            servicios_disponibles='Test Servicios'
        )

        # Crear disponibilidades para la propiedad
        self.fechas_disponibles = [
            date(2024, 11, 25),
            date(2024, 11, 26),
            date(2024, 11, 27)
        ]
        for fecha in self.fechas_disponibles:
            Disponibilidad.objects.create(
                propiedad=self.propiedad,
                fecha=fecha
            )

    def test_crear_reserva_inquilino(self):
        # Crear una reserva válida para un inquilino registrado
        reserva = Reserva.objects.create(
            propiedad=self.propiedad,
            inquilino=self.perfil_usuario,
            numero_huespedes=2,
            fechas_reserva=[str(fecha) for fecha in self.fechas_disponibles[:2]]
        )
        self.assertEqual(reserva.total, 200.00)  # 2 noches x 100
        self.assertEqual(reserva.inquilino, self.perfil_usuario)

    def test_crear_reserva_usuario_anonimo(self):
        # Crear una reserva válida para un usuario anónimo
        reserva = Reserva.objects.create(
            propiedad=self.propiedad,
            nombre_usuario_anonimo="Juan Pérez",
            correo_usuario_anonimo="juan.perez@example.com",
            telefono_usuario_anonimo="123456789",
            numero_huespedes=3,
            fechas_reserva=[str(fecha) for fecha in self.fechas_disponibles[1:]]
        )
        self.assertEqual(reserva.total, 200.00)  # 2 noches x 100
        self.assertEqual(reserva.nombre_usuario_anonimo, "Juan Pérez")

    def test_error_reserva_sin_fechas(self):
        # Intentar crear una reserva sin fechas debería lanzar un error
        with self.assertRaises(ValidationError) as context:
            Reserva.objects.create(
                propiedad=self.propiedad,
                inquilino=self.perfil_usuario,
                numero_huespedes=2,
                fechas_reserva=[]
            )
        self.assertIn("Debe seleccionar al menos una fecha para la reserva.", str(context.exception))

    def test_error_reserva_fechas_no_disponibles(self):
        # Intentar reservar fechas que no están disponibles debería lanzar un error
        with self.assertRaises(ValidationError) as context:
            Reserva.objects.create(
                propiedad=self.propiedad,
                inquilino=self.perfil_usuario,
                numero_huespedes=2,
                fechas_reserva=["2024-11-30"]  # Fecha fuera de las disponibles
            )
        self.assertIn("Una o más fechas seleccionadas no están disponibles.", str(context.exception))

    def test_disponibilidad_se_actualiza_despues_de_la_reserva(self):
        # Verificar que las disponibilidades se eliminan después de crear una reserva
        reserva = Reserva.objects.create(
            propiedad=self.propiedad,
            inquilino=self.perfil_usuario,
            numero_huespedes=2,
            fechas_reserva=[str(fecha) for fecha in self.fechas_disponibles[:2]]
        )
        # Después de la reserva, esas fechas no deberían estar disponibles
        fechas_restantes = Disponibilidad.objects.filter(propiedad=self.propiedad)
        self.assertEqual(fechas_restantes.count(), 1)
        self.assertEqual(fechas_restantes.first().fecha, self.fechas_disponibles[2])

    def test_calculo_total_automatico(self):
        # Verificar que el cálculo del total se realiza automáticamente
        reserva = Reserva.objects.create(
            propiedad=self.propiedad,
            inquilino=self.perfil_usuario,
            numero_huespedes=2,
            fechas_reserva=[str(fecha) for fecha in self.fechas_disponibles[:2]]
        )
        self.assertEqual(reserva.total, 200.00)  # 2 noches x 100