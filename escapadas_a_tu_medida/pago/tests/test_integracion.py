from django.test import TestCase
from django.urls import reverse
from unittest.mock import Mock, patch
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

        self.fechas_disponibles = [
            (date.today() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(5)
        ]
        for fecha in self.fechas_disponibles:
            Disponibilidad.objects.create(propiedad=self.propiedad, fecha=fecha)

        self.fechas_reserva = [self.fechas_disponibles[0]]
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


    @patch('stripe.PaymentIntent.create')
    @patch('stripe.PaymentIntent.retrieve')
    def test_pago_y_reserva_exitoso(self, mock_retrieve_payment_intent, mock_create_payment_intent):
        # Mock para PaymentIntent.create
        mock_create_payment_intent.return_value = {
            'id': 'pi_test',
            'client_secret': 'test_client_secret'
        }

        # Mock para PaymentIntent.retrieve
        mock_payment_intent = Mock()
        mock_payment_intent.id = 'pi_test'
        mock_payment_intent.status = 'succeeded'
        mock_retrieve_payment_intent.return_value = mock_payment_intent

        # Configurar sesión
        session = self.client.session
        session['fechas_reserva'] = self.fechas_reserva
        session['numero_huespedes'] = 2
        session['nombre_cliente'] = 'Juan Pérez'
        session['email_cliente'] = 'juan.perez@example.com'
        session['telefono_cliente'] = '123456789'
        session.save()

        # Solicitar creación de reserva
        response_reserva = self.client.post(
            reverse('crear_reserva_ya_pagada', args=[self.propiedad.id]),
            data={'payment_intent_id': 'pi_test'},
            content_type='application/json'
        )

        # Verificar respuesta
        print(response_reserva.content)  # Para depurar
        self.assertEqual(response_reserva.status_code, 200)
        self.assertEqual(response_reserva.json().get('message'), 'Reserva creada exitosamente.')

        # Validar que la reserva fue creada correctamente
        reserva = Reserva.objects.get(propiedad=self.propiedad)
        self.assertEqual(reserva.numero_huespedes, 2)
        self.assertEqual(reserva.nombre_usuario_anonimo, 'Juan Pérez')
        self.assertEqual(reserva.correo_usuario_anonimo, 'juan.perez@example.com')
        self.assertEqual(reserva.telefono_usuario_anonimo, '123456789')
        self.assertEqual(reserva.fechas_reserva, self.fechas_reserva)
