from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from alquileres.models import Propiedad, Reserva, Disponibilidad
from usuarios.models import PerfilUsuario
from pago.models import Payment
from django.contrib.auth.models import User
from datetime import date, timedelta
import json


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

    @patch('stripe.Webhook.construct_event')
    def test_webhook_pago_exitoso(self, mock_webhook_construct_event):
        # Simula una reserva asociada
        fechas_disponibles = [
            (date.today() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(5)
        ]
        for fecha in fechas_disponibles:
            Disponibilidad.objects.create(propiedad=self.propiedad, fecha=fecha)

        fechas_seleccionadas = [fechas_disponibles[0]]  # Selecciona al menos una fecha disponible

        with patch('alquileres.models.Reserva.save') as mocked_save:
            mocked_save.return_value = None  # Simula que `save()` se ejecuta correctamente
            reserva = Reserva.objects.create(
                fechas_reserva=fechas_seleccionadas,
                numero_huespedes=2,
                total=200.0,
                inquilino=self.inquilino2,
                propiedad=self.propiedad
            )

        # Simula un evento de webhook
        mock_webhook_construct_event.return_value = {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'metadata': {'reserva_id': reserva.id}
                }
            }
        }

        payload = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "metadata": {
                        "reserva_id": reserva.id
                    }
                }
            }
        }
        payload_json = json.dumps(payload)  # Convierte a JSON
        sig_header = 'test_signature'

        response = self.client.post(reverse('stripe_webhook'), data=payload_json, content_type='application/json', HTTP_STRIPE_SIGNATURE=sig_header)

        # Verifica que la reserva se actualiza correctamente
        self.assertEqual(response.status_code, 200)