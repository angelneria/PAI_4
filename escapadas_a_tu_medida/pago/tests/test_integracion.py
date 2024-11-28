from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from alquileres.models import Propiedad, Reserva, Disponibilidad
from usuarios.models import PerfilUsuario
from pago.models import Payment
from django.contrib.auth.models import User
from datetime import date


class TestPagoIntegracion(TestCase):
    def setUp(self):
        # Crear un propietario para la propiedad
        user = User.objects.create_user(
            username="propietario",
            first_name="Propietario",
            last_name="Apellido",
            email="propietario@example.com",
            password="Propietario123!"
        )
        self.propietario = PerfilUsuario.objects.create(
            usuario=user,
            telefono="111111111",
            tipo_usuario="anfitrion"
        )

        # Crear un inquilino que realizará el pago
        self.inquilino = User.objects.create_user(
            username="inquilino",
            first_name="Inquilino",
            last_name="Apellido",
            email="inquilino@example.com",
            password="Inquilino123!"
        )
        PerfilUsuario.objects.create(
            usuario=self.inquilino,
            telefono="222222222",
            tipo_usuario="inquilino"
        )
        user2 = User.objects.create_user(
            username="inquilino2",
            first_name="Inquilino2",
            last_name="Apellido2",
            email="inquilino2@example.com",
            password="Inquilino123!"
        )
        self.inquilino2 = PerfilUsuario.objects.create(
            usuario=user2,
            telefono="333333333",
            tipo_usuario="inquilino"
        )
        # Crear una propiedad asociada al propietario
        self.propiedad = Propiedad.objects.create(
            titulo="Casa de Prueba",
            descripcion="Descripción de prueba",
            ubicacion="Ubicación de prueba",
            precio_por_noche=100.0,
            num_maximo_huespedes=4,
            num_maximo_habitaciones=2,
            servicios_disponibles="Wifi, Piscina",
            tipo="apartamento",
            propietario=self.propietario  # Cambio aquí
        )

        # Crear un pago para el inquilino
        self.payment = Payment.objects.create(
            user=self.inquilino,  # El inquilino realiza el pago
            amount=100.0,
            payment_intent="test_intent_123",
            status="pending"
        )

        # Configurar variables para los tests
        self.monto = 100.0
        self.procesar_pago_url = reverse('procesar_pago', args=[self.propiedad.id, self.monto])


    @patch('stripe.PaymentIntent.create')
    def test_procesar_pago_crea_intent(self, mock_payment_intent_create):
        # Simula la creación del PaymentIntent en Stripe
        mock_payment_intent_create.return_value = {
            'client_secret': 'test_client_secret'
        }

        # Iniciar sesión del inquilino
        self.client.login(username="inquilino", password="Inquilino123!")
        response = self.client.post(self.procesar_pago_url)

        # Verificar que se llama a Stripe con los parámetros correctos
        mock_payment_intent_create.assert_called_once_with(
            amount=int(self.monto * 100),
            currency='eur',
            payment_method_types=['card'],
        )

        # Verificar la respuesta JSON
        self.assertEqual(response.status_code, 200)
        self.assertIn('clientSecret', response.json())

    def test_pagina_pago_renderiza_correctamente(self):
        # Verifica que la página de pago se renderiza correctamente
        self.client.login(username="inquilino", password="Inquilino123!")
        response = self.client.get(self.procesar_pago_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.propiedad.titulo)  # Cambio: usar 'titulo'
        self.assertContains(response, self.monto)

   