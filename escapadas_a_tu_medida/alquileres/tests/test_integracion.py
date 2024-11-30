from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from alquileres.models import Propiedad, Disponibilidad, Reserva, PropiedadesDeseadas
from usuarios.models import PerfilUsuario
from datetime import date, timedelta
from django.core import mail
from pago.models import Payment
from django.test import RequestFactory
from alquileres.views import enviar_correo


class HomeViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Crear usuarios de prueba
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


        # Crear disponibilidades para la propiedad
        for i in range(5):  # 5 días consecutivos disponibles
            Disponibilidad.objects.create(
                propiedad=self.propiedad,
                fecha=date.today() + timedelta(days=i)
            )

    def test_home_view_no_filter(self):
        """
        Verifica que la vista `home` cargue todas las propiedades sin filtros.
        """
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Casa de Prueba')

    def test_home_view_with_filters(self):
        """
        Verifica que la vista `home` aplique correctamente los filtros.
        """
        response = self.client.get(reverse('home'), {
            'ubicacion': 'Ubicación de prueba',
            'precio_min': 50,
            'precio_max': 150,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Casa de Prueba')

        # Caso de filtro sin resultados
        response = self.client.get(reverse('home'), {
            'ubicacion': 'Ciudad No Existente'
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Propiedad de Prueba')

class CrearReservaViewTests(TestCase):
    def setUp(self):
        self.client = Client()

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

        # Crear propiedad de prueba
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

        # Crear un pago para el inquilino
        self.payment = Payment.objects.create(
            user=self.inquilino,  # El inquilino realiza el pago
            amount=100.0,
            payment_intent="test_intent_123",
            status="pending"
        )



        # Crear disponibilidades
        for i in range(5):  # 5 días consecutivos disponibles
            Disponibilidad.objects.create(
                propiedad=self.propiedad,
                fecha=date.today() + timedelta(days=i)
            )

    def test_crear_reserva_view_authenticated_user(self):
        """
        Verifica que un usuario autenticado pueda iniciar el proceso de reserva.
        """
        self.client.login(username="inquilino", password="Inquilino123!")
        fechas_escogidas = f"{date.today()}, {date.today() + timedelta(days=1)}"
        data = {
            'fechas_escogidas': fechas_escogidas,
            'numero_huespedes': 4,
        }

        # Simula un POST para crear una reserva
        response = self.client.post(reverse('crear_reserva', args=[self.propiedad.id]), data)

        # Extrae y procesa las fechas desde el POST
        fechas = [
            date.fromisoformat(f.strip()) for f in data['fechas_escogidas'].split(',')
        ]
        num_noches = (fechas[-1] - fechas[0]).days + 1  # Diferencia de días +1 (incluye ambos días)

        # Calcula dinámicamente el monto basado en las fechas escogidas
        monto_calculado = self.propiedad.precio_por_noche * num_noches

        # Construye la URL esperada con el monto calculado, formateado con dos decimales
        procesar_pago_url = reverse('procesar_pago', args=[self.propiedad.id, f"{monto_calculado:.2f}"])

        # Verificar que se redirige al procesamiento de pago
        self.assertEqual(response.status_code, 302)
        self.assertIn(procesar_pago_url, response.url, msg=f"Expected {procesar_pago_url}, but got {response.url}")

    def test_crear_reserva_view_anonymous_user(self):
        """
        Verifica que un usuario anónimo pueda iniciar el proceso de reserva.
        """
        fechas_escogidas = f"{date.today()}, {date.today() + timedelta(days=1)}"
        data = {
            'fechas_escogidas': fechas_escogidas,
            'numero_huespedes': 4,
            'nombre_usuario_anonimo': 'John Doe',
            'correo_usuario_anonimo': 'aDw0K@example.com',
            'telefono_usuario_anonimo': '1234567890',
        }

        # Simula un POST para crear una reserva
        response = self.client.post(reverse('crear_reserva', args=[self.propiedad.id]), data)

        # Extrae y procesa las fechas desde el POST
        fechas = [
            date.fromisoformat(f.strip()) for f in data['fechas_escogidas'].split(',')
        ]
        num_noches = (fechas[-1] - fechas[0]).days + 1  # Diferencia de días +1 (incluye ambos días)

        # Calcula dinámicamente el monto basado en las fechas escogidas
        monto_calculado = self.propiedad.precio_por_noche * num_noches

        # Construye la URL esperada con el monto calculado, formateado con dos decimales
        procesar_pago_url = reverse('procesar_pago', args=[self.propiedad.id, f"{monto_calculado:.2f}"])

        # Verificar que se redirige al procesamiento de pago
        self.assertEqual(response.status_code, 302)

        # Verificar que la URL de redirección es correcta
        self.assertEqual(response.url, procesar_pago_url)

    def test_crear_reserva_view_invalid_data(self):
        """
        Verifica que la vista maneje correctamente datos no válidos.
        """
        response = self.client.post(reverse('crear_reserva', args=[self.propiedad.id]), {
            'fechas_escogidas': '',  # Fechas vacías
            'numero_huespedes': '',  # Número de huéspedes vacío
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Este campo es obligatorio')  # Verifica un mensaje de error

    def test_crear_reserva_view_availability_check(self):
        """
        Verifica que no se pueda reservar en fechas no disponibles.
        """
        # Marcar todas las disponibilidades como no disponibles
        Disponibilidad.objects.all().delete()

        response = self.client.post(reverse('crear_reserva', args=[self.propiedad.id]), {
            'fechas_escogidas': f"{date.today()}, {date.today() + timedelta(days=1)}",
            'numero_huespedes': 2,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Por favor selecciona al menos una fecha.')

class ConfirmarReservaTestCase(TestCase):
    def setUp(self):
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

        # Crear propiedad de prueba
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
        user = User.objects.create_user(
            username="inquilino",
            first_name="Inquilino",
            last_name="Apellido",
            email="inquilino@example.com",
            password="Inquilino123!"
        )
        self.inquilino = PerfilUsuario.objects.create(
            usuario=user,
            telefono="222222222",
            tipo_usuario="inquilino"
        )

        self.disponibilidad = Disponibilidad.objects.create(
            propiedad=self.propiedad,
            fecha=date.today(),
        )
      
        self.disponibilidad = Disponibilidad.objects.create(
            propiedad=self.propiedad,
            fecha=date.today() + timedelta(days=1),
        )
        
        
        # Generar URL
        self.url = reverse('confirmar_reserva', args=[self.propiedad.id])

    def test_reserva_creada_y_correo_enviado(self):

        factory = RequestFactory()
        request = factory.get('/ruta-de-ejemplo/')
        # Simular sesión y datos
        fechas_escogidas = [date.today().strftime('%Y-%m-%d'), (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')]


        data = {
                    'fechas_reserva': fechas_escogidas,
                    'numero_huespedes': 2,
                    'total': 200.0,
                    'inquilino': self.inquilino,
                    'propiedad': self.propiedad
                }

        reserva = Reserva.objects.create(**data)
        enviar_correo(
            "Confirmación de reserva",
            "test@example.com",
            "Cliente de Pruebas",
            self.propiedad,
            reserva,
            request
        )

        # Verificar que se creó la reserva
        self.assertIsNotNone(reserva)
        self.assertEqual(reserva.propiedad, self.propiedad)

        # Verificar que se envió el correo
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Confirmación de reserva", mail.outbox[0].subject)
        self.assertIn("Cliente de Pruebas", mail.outbox[0].body)
    
class BuscarAlojamientosTestCase(TestCase):
    def setUp(self):
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

        # Crear propiedad de prueba
        self.propiedad = Propiedad.objects.create(
            titulo="Casa Pepe",
            descripcion="Descripción de prueba",
            ubicacion="Madrid",
            precio_por_noche=100.0,
            num_maximo_huespedes=4,
            num_maximo_habitaciones=2,
            servicios_disponibles="Wifi, Piscina",
            tipo="apartamento",
            propietario=self.propietario  # Cambio aquí
        )

        # Crear propiedad de prueba
        self.propiedad1 = Propiedad.objects.create(
            titulo="Casa Paco",
            descripcion="Descripción de prueba",
            ubicacion="Barcelona",
            precio_por_noche=200.0,
            num_maximo_huespedes=4,
            num_maximo_habitaciones=2,
            servicios_disponibles="Wifi, Piscina",
            tipo="apartamento",
            propietario=self.propietario  # Cambio aquí
        )

    def test_busqueda_con_filtros(self):
        response = self.client.get('/buscar/', {'query': 'Casa', 'precio_max': 150})

        # Verificar que sólo una propiedad coincide con el filtro
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Casa Pepe")
        self.assertNotContains(response, "Casa Paco")

class ListaDeseosTestCase(TestCase):
    def setUp(self):
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

        # Crear propiedad de prueba
        self.propiedad = Propiedad.objects.create(
            titulo="Casa Pepe",
            descripcion="Descripción de prueba",
            ubicacion="Madrid",
            precio_por_noche=100.0,
            num_maximo_huespedes=4,
            num_maximo_habitaciones=2,
            servicios_disponibles="Wifi, Piscina",
            tipo="apartamento",
            propietario=self.propietario  # Cambio aquí
        )

        user = User.objects.create_user(
            username="inquilino",
            first_name="Inquilino",
            last_name="Apellido",
            email="inquilino@example.com",
            password="Inquilino123!"
        )
        self.inquilino = PerfilUsuario.objects.create(
            usuario=user,
            telefono="222222222",
            tipo_usuario="inquilino"
        )
    def test_agregar_a_lista_deseos(self):
        self.client.login(username="inquilino", password="Inquilino123!")
        url = reverse('agregar_lista_deseos', args=[self.propiedad.id])
        response = self.client.post(url)

        # Verificar que la propiedad está en la lista de deseos
        self.assertEqual(response.status_code, 302)
        deseos = PropiedadesDeseadas.objects.filter(inquilino=self.inquilino, propiedad=self.propiedad)
        self.assertTrue(deseos.exists())

    def test_eliminar_de_lista_deseos(self):
        self.client.login(username="inquilino", password="Inquilino123!")
        lista_deseos = PropiedadesDeseadas.objects.create()
        lista_deseos.inquilino.add(self.inquilino)
        lista_deseos.propiedad.add(self.propiedad)

        url = reverse('eliminar_lista_deseos', args=[self.propiedad.id])
        response = self.client.post(url)

        # Verificar que se elimina la propiedad de la lista de deseos
        self.assertEqual(response.status_code, 302)
        self.assertFalse(lista_deseos.propiedad.filter(id=self.propiedad.id).exists())

class HistorialReservasTestCase(TestCase):
    def setUp(self):
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

        # Crear propiedad de prueba
        self.propiedad = Propiedad.objects.create(
            titulo="Casa Propietario",
            descripcion="Descripción de prueba",
            ubicacion="Madrid",
            precio_por_noche=100.0,
            num_maximo_huespedes=4,
            num_maximo_habitaciones=2,
            servicios_disponibles="Wifi, Piscina",
            tipo="apartamento",
            propietario=self.propietario  # Cambio aquí
        )

        user = User.objects.create_user(
            username="inquilino",
            first_name="Inquilino",
            last_name="Apellido",
            email="inquilino@example.com",
            password="Inquilino123!"
        )
        self.inquilino = PerfilUsuario.objects.create(
            usuario=user,
            telefono="222222222",
            tipo_usuario="inquilino"
        )
        self.disponibilidad = Disponibilidad.objects.create(
            propiedad=self.propiedad,
            fecha=date.today(),
        )
      
        self.disponibilidad = Disponibilidad.objects.create(
            propiedad=self.propiedad,
            fecha=date.today() + timedelta(days=1),
        )
        self.client.login(username="propietario", password="Propietario123!")
    def test_historial_reservas(self):
        fechas_escogidas = [date.today().strftime('%Y-%m-%d'), (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')]


        data = {
                    'fechas_reserva': fechas_escogidas,
                    'numero_huespedes': 2,
                    'total': 200.0,
                    'inquilino': self.inquilino,
                    'propiedad': self.propiedad
                }

        Reserva.objects.create(**data)
        url = reverse('historial_reservas')
        response = self.client.get(url)

        # Verificar que las reservas del propietario se muestran
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Casa Propietario")