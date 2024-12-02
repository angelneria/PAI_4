
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from alquileres.models import Propiedad, Reserva, Disponibilidad, PropiedadesDeseadas, Imagen
from alquileres.views import calcular_monto
from django.core.exceptions import ValidationError
from django.utils import timezone
from unittest.mock import patch
import stripe
from usuarios.models import PerfilUsuario
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile

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

        self.user2 = get_user_model().objects.create_user(username='usuario2', password='testpassword')

        self.perfil_usuario2 = PerfilUsuario.objects.create(
            usuario=self.user2,
            tipo_usuario="inquilino"
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
            tipo = 'apartamento',
            servicios_disponibles='Wifi, Piscina'
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
        self.imagen =Imagen.objects.create(propiedad=self.propiedad, imagen='escapadas_a_tu_medida/media/navbar.jpg')

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_crear_reserva_view_authenticated(self):
        # Autenticamos al usuario
        self.client.login(username='usuario2', password='testpassword')

        # Realizamos una reserva
        data = {
            'fechas_escogidas': '2025-12-01, 2025-12-02',
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
            'fechas_reserva': '2025-12-01, 2025-12-02',
            'numero_huespedes': 4,
            'nombre_usuario_anonimo': 'Pepe Antonio',
            'correo_usuario_anonimo': '4o0QI@example.com',
            'telefono_usuario_anonimo': '123456789'
        }
        response = self.client.post(reverse('crear_reserva', args=[self.propiedad.id]), data)

        # Comprobamos que redirige al login
        self.assertEqual(response.status_code, 302)


    @patch('cloudinary.uploader.upload')
    def test_crear_propiedad_valida(self, mock_upload):
        mock_upload.return_value = {
        'url': 'http://res.cloudinary.com/test_image.jpg',
        'secure_url': 'https://res.cloudinary.com/test_image.jpg',
    }
        # Iniciar sesión con el usuario anfitrión
        self.client.login(username='usuario', password='testpassword')

        # Definir los datos del formulario para la nueva propiedad
        propiedad_data = {
            'titulo': 'Casa en el bosque',
            'descripcion': 'Una casa tranquila en el bosque',
            'ubicacion': 'Bosque de los Álamos',
            'precio_por_noche': 120.00,
            'num_maximo_huespedes': 4,
            'num_maximo_habitaciones': 2,
            'servicios_disponibles': 'Calefacción, Wifi',
            'tipo': 'casa',
            'fechas_disponibles': '2025-12-01, 2025-12-02',
        }

        # Crear las imágenes a subir (utilizando el archivo de prueba creado)
        with open('media/navbar.jpg', 'rb') as f:
            imagenes = [SimpleUploadedFile('navbar.jpg', f.read(), content_type='image/jpeg')]

        # Realizar la solicitud POST con los datos del formulario y las imágenes
        response = self.client.post(reverse('crear_propiedad'), {
            **propiedad_data,
            'imagenes': imagenes,
        })

        # Verificar que la propiedad ha sido creada correctamente
        self.assertEqual(response.status_code, 302)  # Redirige correctamente
        self.assertEqual(Propiedad.objects.count(), 2)  # Ahora debería haber 2 propiedades
        propiedad = Propiedad.objects.last()
        self.assertEqual(propiedad.titulo, 'Casa en el bosque')
        self.assertEqual(propiedad.descripcion, 'Una casa tranquila en el bosque')
        self.assertEqual(propiedad.precio_por_noche, 120.00)
        self.assertEqual(propiedad.num_maximo_huespedes, 4)
        self.assertEqual(propiedad.num_maximo_habitaciones, 2)
        self.assertEqual(propiedad.servicios_disponibles, 'Calefacción, Wifi')
        self.assertEqual(propiedad.tipo, 'casa')
        self.assertEqual(propiedad.disponibilidades.count(), 2)  # Verifica que las fechas de disponibilidad fueron creadas
        self.assertEqual(propiedad.imagenes.count(), 1) 




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
                'descripcion': 'Hermosa casa con nueva descripción',
                'ubicacion': 'Playa de Palma, Mallorca',
                'precio_por_noche': 120.00,
                'num_maximo_huespedes': 6,
                'num_maximo_habitaciones': 3,
                'servicios_disponibles': 'Wifi, Piscina',
                'tipo' : 'apartamento',
                # Agregar otros campos necesarios aquí si el formulario los requiere
            }
        )

        # Verificar que el formulario se procesa (no estamos verificando la redirección aquí)
        self.assertRedirects(response, '/')  # No estamos verificando el código 302 de redirección
        
        # Verificar que la propiedad se ha actualizado
        self.propiedad.refresh_from_db()  # Recargar la propiedad desde la base de datos
        self.assertEqual(self.propiedad.titulo, 'Casa en la playa actualizada')
        self.assertEqual(self.propiedad.descripcion, 'Hermosa casa con nueva descripción')
        self.assertEqual(self.propiedad.ubicacion, 'Playa de Palma, Mallorca')
        self.assertEqual(self.propiedad.precio_por_noche, 120.00)






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
        self.client.login(username='usuario2', password='testpassword')
        self.client.post(reverse('agregar_lista_deseos', args=[self.propiedad.id]))
        propiedad_deseada = PropiedadesDeseadas.objects.filter(inquilino=self.perfil_usuario2, propiedad=self.propiedad)
        self.assertTrue(propiedad_deseada.exists())



    def test_eliminar_de_lista_deseos(self):
    # Iniciar sesión como el usuario
        self.client.login(username='usuario2', password='testpassword')

       
        # Realizar la solicitud POST para eliminar la propiedad de la lista de deseos
        response = self.client.post(reverse('eliminar_lista_deseos', args=[self.propiedad.id]))

        # Verificar que la respuesta sea una redirección
        self.assertEqual(response.status_code, 302)

        # Verificar que la propiedad ya no está en la lista de deseos
        self.assertFalse(PropiedadesDeseadas.objects.filter(id=self.propiedad.id).exists())





    def test_valorar_propiedad(self):
        self.client.login(username='usuario2', password='testpassword')
        data = {'calificacion': 4}
        response = self.client.post(reverse('valorar_propiedad', args=[self.propiedad.id]), data)


        self.assertEqual(response.status_code, 302)        

        # Verificar que la valoración se ha creado correctamente
        valoracion = self.propiedad.valoraciones.filter(usuario=self.perfil_usuario2)
        self.assertTrue(valoracion.exists())
        self.assertEqual(valoracion.first().calificacion, 4)