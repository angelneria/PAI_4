from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from django.http import JsonResponse
from alquileres.models import Propiedad, PerfilUsuario
from django.contrib.auth.models import User

from django.conf import settings


class PagoTestCase(TestCase):

    @patch('stripe.PaymentIntent.create')
    def test_procesar_pago_post(self, mock_payment_intent_create):
        # Datos de la prueba
        propiedad_id = 1
        monto = 100.00

        self.client.login(username='usuario', password='testpassword')

        # Creamos un usuario para ser el propietario
        propietario = PerfilUsuario.objects.create(
            usuario= User.objects.create_user(username='testuser', password='testpassword'),
            tipo_usuario='anfitrion',
            telefono='1234567890'
        )
        
        # Creamos una propiedad de prueba en la base de datos
        propiedad = Propiedad.objects.create(
            titulo="Casa en la playa", 
            descripcion="Hermosa casa junto al mar", 
            ubicacion="Playa de Palma", 
            precio_por_noche=100, 
            num_maximo_huespedes=6,
            num_maximo_habitaciones=3,
            servicios_disponibles="Wifi, Piscina", 
            tipo="casa",
            propietario= propietario
        )

        # Simulamos que Stripe crea un PaymentIntent correctamente
        mock_payment_intent_create.return_value = {
            'client_secret': 'fake_client_secret'
        }
        
        # Realizamos la petición POST
        response = self.client.post(reverse('procesar_pago', args=[propiedad.id, monto]))
        
        # Comprobamos que Stripe fue llamado
        mock_payment_intent_create.assert_called_once_with(
            amount=int(monto * 100),  # Stripe espera el monto en céntimos
            currency='eur',
            payment_method_types=['card'],
        )

        # Verificamos que la respuesta contiene el clientSecret
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['clientSecret'], 'fake_client_secret')

    def test_procesar_pago_get(self):
        # Datos de la prueba
        propiedad_id = 1
        monto = 100.00
        
        propietario = PerfilUsuario.objects.create(
            usuario= User.objects.create_user(username='testuser', password='testpassword'),
            tipo_usuario='anfitrion',
            telefono='1234567890'
        )
        
        # Creamos una propiedad de prueba en la base de datos
        propiedad = Propiedad.objects.create(
            titulo="Casa en la playa", 
            descripcion="Hermosa casa junto al mar", 
            ubicacion="Playa de Palma", 
            precio_por_noche=100, 
            num_maximo_huespedes=6,
            num_maximo_habitaciones=3,
            servicios_disponibles="Wifi, Piscina", 
            tipo="casa",
            propietario= propietario
        )

        # Realizamos la petición GET
        response = self.client.get(reverse('procesar_pago', args=[propiedad.id, monto]))
        
        # Comprobamos que el template correcto se ha renderizado
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pago.html')

        # Verificamos que los datos están en el contexto
        self.assertContains(response, settings.STRIPE_PUBLIC_KEY)
        self.assertContains(response, str(monto))
        