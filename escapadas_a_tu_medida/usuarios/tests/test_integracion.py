from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario
from django.shortcuts import redirect
from usuarios.forms import (
    FormularioRegistroUsuario,
    FormularioInicioSesion,
    FormularioEdicionUsuario,
    FormularioEdicionPerfilUsuario,
)

class TestRegistroUsuario(TestCase):

    def setUp(self):
        self.valid_data = {
            "username": "usuario1",
            "email": "usuario1@example.com",
            "first_name": "Usuario",
            "last_name": "Apellido",
            "password": "Password123!",
            "confirmar_password": "Password123!",
            "telefono": "123456789",
            "tipo_usuario": "inquilino",
        }

    def test_registro_usuario_valido(self):
        url = reverse('registro')  # URL del formulario de registro
        response = self.client.post(url, self.valid_data)

        # Verificar que el formulario ha sido enviado correctamente y redirige
        self.assertEqual(response.status_code, 302)  # Redirige después del registro
        self.assertRedirects(response, '/')  # Redirige a la página de inicio (usa la URL directa)
        self.assertTrue(User.objects.filter(username='usuario1').exists())  # El usuario se ha creado


class TestInicioSesion(TestCase):
    def setUp(self):
        # Crear usuario
        self.user = User.objects.create_user(username="usuario1", password="Password123!")
        
        # Crear el perfil asociado al usuario
        PerfilUsuario.objects.create(usuario=self.user, telefono="123456789", tipo_usuario="inquilino")

    def test_inicio_sesion_valido(self):
        url = reverse('iniciar_sesion')
        data = {
            'username': 'usuario1',
            'password': 'Password123!',
        }
        response = self.client.post(url, data)

        # Verificar que el inicio de sesión fue exitoso
        self.assertEqual(response.status_code, 302)  # Redirección al perfil u otra página protegida
        self.assertRedirects(response, '/')  # Redirige al home


class TestEdicionPerfil(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="usuario", first_name="Nombre", last_name="Apellido", email="usuario@example.com", password="Password123!")
        PerfilUsuario.objects.create(usuario=self.user, telefono="123456789", tipo_usuario="inquilino")
        self.client.login(username='usuario', password='Password123!')

    def test_editar_perfil_valido(self):
        url = reverse('editar_perfil')
        
        response = self.client.post(url, {
            "username": "updateduser",
            "email": "updateduser@example.com",
            "telefono": "111222333",
            "tipo_usuario": "inquilino"
        })

        # Verificar que el perfil fue editado correctamente
        self.assertRedirects(response, '/')
        self.assertEqual(response.status_code, 302)  # Redirección al perfil después de editar
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')
        self.assertEqual(self.user.perfilusuario.telefono, '111222333')
        self.assertEqual(self.user.email, 'updateduser@example.com')


class TestRedireccionVista(TestCase):
    def test_no_acceso_sin_autenticacion(self):
        # Intentar acceder a la página de perfil sin estar autenticado
        url = reverse('editar_perfil')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirige a login

        # Intentar acceder a la página de chat sin estar autenticado
        url = reverse('lista_chats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirige a login
