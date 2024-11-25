import os
import json
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'escapadas_a_tu_medida.settings')
django.setup()
from locust import HttpUser, task, between
from django.contrib.auth import get_user_model
from usuarios.models import PerfilUsuario
from django.urls import reverse

class UsuarioDjango(HttpUser):
    wait_time = between(1, 2)  # 1 a 2 segundos entre cada solicitud
    host = "http://localhost:8000/"
    
    def on_start(self):
        """ Crear usuarios para simular la carga """
        user_model = get_user_model()

        # Crear usuario 1 (inquilino)
        self.user1, created = user_model.objects.get_or_create(username="usuario_inquilino")
        if created:
            self.user1.set_password("testpassword")
            self.user1.save()
            self.perfil_usuario1 = PerfilUsuario.objects.create(usuario=self.user1, tipo_usuario="inquilino")
        
        # Crear usuario 2 (anfitrión)
        self.user2, created = user_model.objects.get_or_create(username="usuario_anfitrion")
        if created:
            self.user2.set_password("testpassword")
            self.user2.save()
            self.perfil_usuario2 = PerfilUsuario.objects.create(usuario=self.user2, tipo_usuario="anfitrion")

        # Realizar login para el usuario 1
        self.client.post("/login/", {"username": self.user1.username, "password": "testpassword"})
    
    @task(1)
    def test_registro(self):
        """ Prueba de carga para la vista de registro """
        form_data = {
            "username": "nuevo_usuario",
            "email": "nuevo@usuario.com",
            "password": "password123",
            "first_name": "Nuevo",
            "last_name": "Usuario",
            "tipo_usuario": "inquilino",
            "telefono": "123456789"
        }
        self.client.post("/registro/", form_data)
    
    @task(1)
    def test_iniciar_sesion(self):
        """ Prueba de carga para la vista de inicio de sesión """
        self.client.post("/login/", {
            "username": self.user2.username,
            "password": "testpassword"
        })
    
    @task(1)
    def test_editar_perfil(self):
        """ Prueba de carga para la vista de editar perfil """
        self.client.post("/login/", {
        "username": self.user2.username,
        "password": "testpassword"
        })
        form_data = {
            "username": "usuario_anfitrion_editado",
            "first_name": "Nombre Editado",
            "last_name": "Apellido Editado",
            "email": "nuevo_email@dominio.com",
            "telefono": "987654321"
        }
        self.client.post("/perfil/", form_data)

    @task(1)
    def test_logout(self):
        """ Prueba de carga para la vista de logout """
        self.client.get("/logout/")

    @task(1)
    def test_lista_chats(self):
        self.client.post("/login/", {
        "username": self.user2.username,
        "password": "testpassword"
        })
        """ Prueba de carga para la vista de lista de chats """
        self.client.get("/chat/")



    @task(1)
    def test_send_message(self):
        """ Prueba de carga para enviar un mensaje en un chat """
        room_name = "chat_1_2"
        message_data = {
            "content": "¡Hola! Este es un mensaje de prueba"
        }
        self.client.post(f"/chat/{room_name}/send/", json.dumps(message_data), headers={"Content-Type": "application/json"})

