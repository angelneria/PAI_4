import json
from django.test import TestCase, Client
from django.urls import reverse
from usuarios.models import PerfilUsuario, Message
from django.contrib.auth import get_user_model

from django.utils import timezone


User = get_user_model()

class ChatViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Crear usuarios
        self.inquilino = User.objects.create_user(username="inquilino", password="pass1234")
        self.anfitrion = User.objects.create_user(username="anfitrion", password="pass1234")

        # Crear perfiles
        self.perfil_inquilino = PerfilUsuario.objects.create(usuario=self.inquilino, tipo_usuario="inquilino")
        self.perfil_anfitrion = PerfilUsuario.objects.create(usuario=self.anfitrion, tipo_usuario="anfitrion")

        # URLs
        self.lista_chats_url = reverse("lista_chats")
        self.get_messages_url = lambda room_name: reverse("get_messages", kwargs={"room_name": room_name})
        self.send_message_url = lambda room_name: reverse("send_message", kwargs={"room_name": room_name})
        self.chat_view_url = lambda room_name: reverse("chat_view", kwargs={"room_name": room_name})


    def test_get_messages(self):
        self.client.login(username="inquilino", password="pass1234")

        # Crear mensajes en una sala
        room_name = f"chat_{self.inquilino.id}_{self.anfitrion.id}"
        Message.objects.create(
            room=room_name, sender="inquilino", content="Hola", timestamp=timezone.now()
        )

        response = self.client.get(self.get_messages_url(room_name))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["messages"]), 1)
        self.assertEqual(data["messages"][0]["content"], "Hola")


    def test_lista_chats_para_inquilino(self):
        # Autenticar como inquilino
        self.client.login(username="inquilino", password="pass1234")
        
        # Crear un mensaje para probar el último mensaje
        room_name = f"chat_{self.inquilino.id}_{self.anfitrion.id}"
        Message.objects.create(room=room_name, sender="anfitrion", content="Hola", timestamp=timezone.now())
        
        # Solicitar lista de chats
        response = self.client.get(self.lista_chats_url)
        self.assertEqual(response.status_code, 200)
        
        # Comprobar contenido del contexto
        chats = response.context["chats"]
        self.assertEqual(len(chats), 1)  # Hay un solo anfitrión
        self.assertEqual(chats[0]["ultimo_mensaje"], "Hola")  # El último mensaje es correcto


    def test_send_message(self):
        self.client.login(username="inquilino", password="pass1234")
        
        # Crear sala de chat
        room_name = f"chat_{self.inquilino.id}_{self.anfitrion.id}"
        data = {"content": "Este es un mensaje de prueba"}
        
        response = self.client.post(
            self.send_message_url(room_name),
            data=json.dumps(data),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        
        # Comprobar que el mensaje se creó en la base de datos
        mensaje = Message.objects.get(room=room_name)
        self.assertEqual(mensaje.content, "Este es un mensaje de prueba")
        self.assertEqual(mensaje.sender, self.inquilino.username)



