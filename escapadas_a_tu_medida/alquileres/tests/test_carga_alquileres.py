import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escapadas_a_tu_medida.settings')
django.setup()
from locust import HttpUser, task, between
from django.contrib.auth import get_user_model
from usuarios.models import PerfilUsuario
from alquileres.models import Propiedad, Disponibilidad, Imagen, PropiedadesDeseadas
from bs4 import BeautifulSoup 
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

class UsuarioDjango(HttpUser):
    wait_time = between(1, 2)  # 1 a 2 segundos entre cada solicitud
    host = "http://localhost:8000/"

    def on_start(self):
        # Crear los usuarios solo si no existen
        user_model = get_user_model()

        # Verificar si el usuario ya existe
        self.user, created = user_model.objects.get_or_create(username='usuario')
        if created:
            self.user.set_password('testpassword')
            self.user.save()

        self.perfil_usuario, created = PerfilUsuario.objects.get_or_create(
            usuario=self.user, tipo_usuario="anfitrion"
        )

        self.user2, created = user_model.objects.get_or_create(username='usuario2')
        if created:
            self.user2.set_password('testpassword')
            self.user2.save()

        self.perfil_usuario2, created = PerfilUsuario.objects.get_or_create(
            usuario=self.user2, tipo_usuario="inquilino"
        )

        # Realizar login en el sistema con el token CSRF
        self.client.post("login/", {
            "username": self.user.username,
            "password": 'testpassword',
        })

       

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
    
    @task(1)
    def home_con_filtros(self):
            # Filtros que vamos a usar en la búsqueda
            params = {
                "ubicacion": "Madrid",  # Puedes modificarlo a cualquier ciudad o lugar
                "precio_min": 50,
                "precio_max": 300,
                "num_maximo_huespedes": 4,
                "num_maximo_habitaciones": 2,
                "tipo": "apartamento",
                "valoracion_minima": 4
            }

            self.client.get("", params=params)
    
    @task(1)
    def acceso_home(self):
        # Simular una solicitud GET a la página principal
        self.client.get("")  # O cualquier otro endpoint que quieras probar

    @task(1)
    def crear_reserva(self):
            # Parámetros para la creación de reserva
            fechas_escogidas = "2024-12-01, 2024-12-02"  # Fechas seleccionadas para la reserva
            numero_huespedes = 2  # Número de huéspedes

            # Realizar la solicitud POST para crear una reserva
            self.client.post(f"reservar/{self.propiedad.id}/", {
                "fechas_escogidas": fechas_escogidas,
                "numero_huespedes": numero_huespedes,
            })

    @task(1)
    def ver_historial_reservas(self):
        # Solicitar el historial de reservas del usuario
        response = self.client.get("/historialReservas/")
        # Si la respuesta es exitosa (200 OK), seguimos con la simulación
        assert response.status_code == 200
    
    @task(1)
    def test_buscar_alojamientos(self):
        # Definir los parámetros de búsqueda para la tarea
        params = {
            "query": "Playa",  # Término de búsqueda
            "ubicacion": "Madrid",
            "precio_min": 50,
            "precio_max": 300,
            "num_maximo_huespedes": 4,
            "num_maximo_habitaciones": 2,
            "tipo": "apartamento",
            "valoracion_minima": 4
        }
        
        # Realizar la solicitud GET a la página de búsqueda con los parámetros
        self.client.get("/buscar/", params=params)

    @task(1)
    def test_buscar_sin_filtros(self):
        # Realizar búsqueda sin filtros
        self.client.get("/buscar/")  # Puede cambiar si la URL es distinta

    @task(1)
    def test_crear_propiedad(self):
        """Simula la creación de una propiedad con imágenes y fechas disponibles"""
        
        # Crear datos aleatorios para la propiedad
        nombre_propiedad = "Propiedad"
        descripcion = "Una hermosa propiedad para alquilar."
        ubicacion = "Madrid"
        precio = 100.0
        max_huespedes = 4
        max_habitaciones = 2

        # Fechas disponibles (simulando que el propietario pone dos fechas disponibles)
        fechas_disponibles = "2024-12-01, 2024-12-02"

        # Crear imágenes de prueba (puedes usar imágenes reales si deseas)
        imagenes = [SimpleUploadedFile("test_image.jpg", b"Imagen de prueba", content_type="image/jpeg")]

        # Preparar datos del formulario
        propiedad_data = {
            "titulo": nombre_propiedad,
            "descripcion": descripcion,
            "ubicacion": ubicacion,
            "precio_por_noche": precio,
            "num_maximo_huespedes": max_huespedes,
            "num_maximo_habitaciones": max_habitaciones,
            "fechas_disponibles": fechas_disponibles,
        }

        imagenes = [SimpleUploadedFile("test_image.jpg", b"Imagen de prueba", content_type="image/jpeg")]

        # Realizar la solicitud POST con los datos del formulario y las imágenes
        response = self.client.post(reverse('crear_propiedad'), {
            **propiedad_data,
            'imagenes': imagenes,
        })
        assert response.status_code == 200  # Verificar que la respuesta sea 200


    @task(1)
    def test_listar_propiedades(self):
        response = self.client.get("gestionPropiedad/")  # Ajusta la URL según tu configuración
        assert response.status_code == 200 

    @task(1)
    def test_eliminar_propiedad(self):
        propiedad = Propiedad.objects.create(
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
            propiedad=propiedad,
            fecha=timezone.now().date() + timezone.timedelta(days=1)
        )
        disponibilidad2 = Disponibilidad.objects.create(
            propiedad=propiedad,
            fecha=timezone.now().date() + timezone.timedelta(days=2)
        )
        imagen =Imagen.objects.create(propiedad=propiedad, imagen='escapadas_a_tu_medida/media/navbar.jpg')
        self.client.post(f"/gestionPropiedad/delete/{propiedad.id}/")
    @task(1)
    def test_actualizar_propiedad(self):
        """Simular actualización de una propiedad"""
        # Obtener detalles actuales de la propiedad
        if self.perfil_usuario.tipo_usuario == "anfitrion":
            # Realizar la solicitud GET y POST con user2 (el inquilino)
            self.client.post("login/", {
                "username": self.user.username,
                "password": 'testpassword',
            })  # Asegura que está logueado como user2
        self.client.get(f"/gestionPropiedad/update/{self.propiedad.id}/")

     
        self.client.post(f"/gestionPropiedad/update/{self.propiedad.id}/", {
            "titulo": "Propiedad Actualizada",
            "descripcion": "Descripción actualizada",
            "ubicacion": "Nueva ubicación",
            "precio_por_noche": 120.0,
            "num_maximo_huespedes": 5,
            "num_maximo_habitaciones": 3,
        })

    @task(1)
    def test_mostrar_detalles_propiedad(self):
        """Simular la visualización de detalles de la propiedad"""
        self.client.get(f"/gestionPropiedad/show/{self.propiedad.id}/")

    @task(1)
    def test_agregar_a_lista_deseos(self):
        """Simular la adición de una propiedad a la lista de deseos"""
        if self.perfil_usuario2.tipo_usuario == "inquilino":
            # Realizar la solicitud GET y POST con user2 (el inquilino)
            self.client.post("login/", {
                "username": self.user2.username,
                "password": 'testpassword',
            })  # Asegura que está logueado como user2
            
            self.client.get(f"/agregarListaDeseos/{self.propiedad.id}/")
            self.client.post(f"/agregarListaDeseos/{self.propiedad.id}/")

    @task(1)
    def test_obtener_lista_deseos(self):
        """Simular la obtención de la lista de deseos"""
        if self.perfil_usuario2.tipo_usuario == "inquilino":
            # Realizar la solicitud GET y POST con user2 (el inquilino)
            self.client.post("login/", {
                "username": self.user2.username,
                "password": 'testpassword',
            })  
        self.client.get("/listaDeseos/")

    @task(1)
    def test_eliminar_de_lista_deseos(self):
        """Simular la eliminación de una propiedad de la lista de deseos"""

        # Obtener el perfil del usuario inquilino
        perfil_inquilino = self.perfil_usuario2  # user2 es el inquilino

        # Crear la relación entre el inquilino y la propiedad en la lista de deseos
        propiedad_deseada = PropiedadesDeseadas.objects.create()
        propiedad_deseada.inquilino.add(perfil_inquilino)
        propiedad_deseada.propiedad.add(self.propiedad)

        # Verificar que la relación exista antes de eliminarla
        assert PropiedadesDeseadas.objects.filter(
            inquilino=perfil_inquilino, propiedad=self.propiedad
        ).exists()

        # Simular la eliminación de la propiedad de la lista de deseos
        self.client.get(f"/eliminarListaDeseos/{self.propiedad.id}/")
        self.client.post(f"/eliminarListaDeseos/{self.propiedad.id}/")

    

        