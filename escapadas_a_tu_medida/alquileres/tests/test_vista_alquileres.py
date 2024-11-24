from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from alquileres.models import Propiedad, Reserva, Disponibilidad, PropiedadesDeseadas, PerfilUsuario
from alquileres.views import calcular_monto
from django.core.exceptions import ValidationError
from django.utils import timezone
from unittest.mock import patch
import stripe

# Simulamos el pago en Stripe
stripe.PaymentIntent.create = patch("stripe.PaymentIntent.create", return_value={"client_secret": "test_client_secret"})

class ReservaViewTests(TestCase):

    def setUp(self):
        # Crear un usuario de prueba
        self.user = get_user_model().objects.create_user(username='usuario', password='testpassword')

        self.perfil_usuario = PerfilUsuario.objects.create(
            usuario=self.user,
            tipo_usuario="anfitrion"
        )

        # Crear una propiedad de prueba
        self.propiedad = Propiedad.objects.create(
            titulo="Casa en la playa",
            descripcion="Hermosa casa junto al mar",
            ubicacion="Playa de Palma",
            precio_por_noche=100.00,
            num_maximo_huespedes=6,
            num_maximo_habitaciones=3,
            propietario=self.perfil_usuario,
        )

        # Crear fechas disponibles para la propiedad
        disponibilidad1 = Disponibilidad.objects.create(
            propiedad=self.propiedad,
            fecha=timezone.now().date() + timezone.timedelta(days=1)
        )
        disponibilidad2 = Disponibilidad.objects.create(
            propiedad=self.propiedad,
            fecha=timezone.now().date() + timezone.timedelta(days=2)
        )

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_crear_reserva_view_authenticated(self):
        # Autenticamos al usuario
        self.client.login(username='usuario', password='testpassword')

        # Realizamos una reserva
        data = {
            'fechas_escogidas': '2024-12-01, 2024-12-02',
            'numero_huespedes': 4,
            'monto': '200.0'
        }
        response = self.client.post(reverse('crear_reserva', args=[self.propiedad.id]), data)

        # Comprobamos que redirige a la vista de pago
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('procesar_pago', args=[self.propiedad.id, '200.00']))

    def test_crear_reserva_view_unauthenticated(self):
        # Usuario no autenticado
        data = {
            'fechas_escogidas': '2024-12-01, 2024-12-02',
            'numero_huespedes': 4,
        }
        response = self.client.post(reverse('crear_reserva', args=[self.propiedad.id]), data)

        # Comprobamos que redirige al login
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('crear_reserva', args=[self.propiedad.id]))



    def test_crear_propiedad_view_authenticated(self):
        # Autenticamos al usuario
        self.client.login(username='usuario', password='testpassword')

        # Datos del formulario de propiedad
        data = {
            'titulo': 'Nuevo alojamiento',
            'descripcion': 'Descripción del nuevo alojamiento',
            'ubicacion': 'Madrid',
            'precio_por_noche': 150.00,
            'num_maximo_huespedes': 5,
            'num_maximo_habitaciones': 2,
        }

        response = self.client.post(reverse('crear_propiedad'), data)

        # Verificamos que la propiedad se crea correctamente y redirige
        self.assertRedirects(response, '/')
        self.assertTrue(Propiedad.objects.filter(titulo='Nuevo alojamiento').exists())




    def test_listar_propiedades_propietario(self):
        self.client.login(username='usuario', password='testpassword')
        response = self.client.get(reverse('listar_propiedades_propietario'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.propiedad.titulo)

    def test_actualizar_propiedad(self):
        self.client.login(username='usuario', password='testpassword')
        
        # Simular la actualización de la propiedad
        response = self.client.post(
            reverse('editar_propiedad', args=[self.propiedad.id]),
            {
                'titulo': 'Casa en la playa actualizada',
            }
        )

        # Verificar la redirección tras la actualización
        self.assertRedirects(response, '/')

        
        

        # Comprobar que el título se ha actualizado
        self.assertEqual(self.propiedad.titulo, 'Casa en la playa actualizada')


    def test_eliminar_propiedad(self):
        self.client.login(username='usuario', password='testpassword')
        response = self.client.post(reverse('eliminar_propiedad', args=[self.propiedad.id]))
        self.assertRedirects(response, '/gestionPropiedad/')
        with self.assertRaises(Propiedad.DoesNotExist):
            self.propiedad.refresh_from_db()

    def test_mostrar_detalles_propiedad(self):
        response = self.client.get(reverse('mostrar_propiedad', args=[self.propiedad.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.propiedad.titulo)
        self.assertContains(response, self.propiedad.descripcion)

    def test_agregar_a_lista_deseos(self):
        self.client.login(username='usuario', password='testpassword')
        self.client.post(reverse('agregar_lista_deseos', args=[self.propiedad.id]))
        propiedad_deseada = PropiedadesDeseadas.objects.filter(inquilino=self.perfil_usuario, propiedad=self.propiedad)
        self.assertTrue(propiedad_deseada.exists())



    def test_eliminar_de_lista_deseos(self):
        self.client.login(username='usuario', password='testpassword')
        propiedad_deseada = PropiedadesDeseadas.objects.create()
        propiedad_deseada.inquilino.add(self.perfil_usuario)
        propiedad_deseada.propiedad.add(self.propiedad)

        response = self.client.post(reverse('eliminar_lista_deseos', args=[self.propiedad.id]))
        self.assertRedirects(response, '/listaDeseos')
        with self.assertRaises(PropiedadesDeseadas.DoesNotExist):
            propiedad_deseada.refresh_from_db()

    def test_valorar_propiedad(self):
        self.client.login(username='usuario', password='testpassword')
        data = {'calificacion': 4}
        response = self.client.post(reverse('valorar_propiedad', args=[self.propiedad.id]), data)
        self.assertRedirects(response, reverse('mostrar_propiedad', args=[self.propiedad.id]))
        valoracion = self.propiedad.valoracion_set.filter(usuario=self.perfil_usuario)
        self.assertTrue(valoracion.exists())
        self.assertEqual(valoracion.first().calificacion, 4)








