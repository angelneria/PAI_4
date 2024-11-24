from django.test import TestCase, Client
from django.urls import reverse
from usuarios.models import PerfilUsuario, User
from django.contrib.auth import get_user_model

class UsuarioViewsTest(TestCase):
    def setUp(self):
        # Configurar un cliente de pruebas
        self.client = Client()
        
        # Crear un usuario de prueba
        self.user = get_user_model().objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="password123",
            first_name="Test",
            last_name="User"
        )
        
        # Crear perfil asociado
        self.perfil = PerfilUsuario.objects.create(
            usuario=self.user,
            tipo_usuario="inquilino",
            telefono="123456789"
        )
        
        # URLs de las vistas
        self.registro_url = reverse("registro")
        self.iniciar_sesion_url = reverse("iniciar_sesion")
        self.editar_perfil_url = reverse("editar_perfil")
        self.logout_url = reverse("logout")
        self.password_reset_url = reverse("password_reset")
        self.password_reset_done_url = reverse("password_reset_done")
        self.password_reset_confirm_url = "password_reset_confirm"
        self.password_reset_complete_url = reverse("password_reset_complete")

    def test_registro_usuario_valido(self):
        # Datos de prueba
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "Password123!",
            "confirmar_password": "Password123!",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "tipo_usuario": "inquilino",  # Una de las opciones válidas
            "telefono": "987654321"
        }
        
        # Enviar solicitud POST
        response = self.client.post(self.registro_url, data)
        
        # Asegúrate de que redirige (código de estado 302)
        self.assertEqual(response.status_code, 302)
        
        # Verifica que el usuario fue creado
        self.assertTrue(get_user_model().objects.filter(username="newuser").exists())
        
        # Verifica que el perfil fue creado
        perfil = PerfilUsuario.objects.get(usuario__username="newuser")
        self.assertEqual(perfil.tipo_usuario, "inquilino")
        self.assertEqual(perfil.telefono, "987654321")



    def test_registro_usuario_invalido(self):

        response = self.client.post(self.registro_url, {
            "username": "",  # Sin nombre de usuario
            "email": "invalidemail",
            "password": "short",
        })
        self.assertEqual(response.status_code, 200)  # No redirige, permanece en la página
        self.assertContains(response, "Este campo es obligatorio.")  # Mensaje de error esperado

    def test_iniciar_sesion_valido(self):

        response = self.client.post(self.iniciar_sesion_url, {
            "username": "testuser",
            "password": "password123",
        })
        self.assertEqual(response.status_code, 302)  # Redirige después del inicio de sesión
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_iniciar_sesion_invalido(self):

        response = self.client.post(self.iniciar_sesion_url, {
            "username": "testuser",
            "password": "wrongpassword",
        })
        self.assertEqual(response.status_code, 200)  # No redirige, permanece en la página
        self.assertContains(response, "Usuario o contraseña incorrectos.")

    def test_editar_perfil_valido(self):

        self.client.login(username="testuser", password="password123")
        response = self.client.post(self.editar_perfil_url, {
            "username": "updateduser",
            "email": "updateduser@example.com",
            "telefono": "111222333",
            "tipo_usuario": "inquilino"
        })
        self.assertEqual(response.status_code, 302)  # Redirige después de editar el perfil
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "updateduser")
        self.assertEqual(self.user.email, "updateduser@example.com")
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.telefono, "111222333")

    def test_editar_perfil_invalido(self):

        self.client.login(username="testuser", password="password123")
        response = self.client.post(self.editar_perfil_url, {
            "username": "",  # Nombre de usuario vacío
            "email": "notanemail"
        })
        self.assertEqual(response.status_code, 200)  # No redirige, permanece en la página
        self.assertContains(response, "Este campo es obligatorio.")  # Mensaje de error esperado

    def test_logout(self):

        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)  # Redirige después del cierre de sesión
        self.assertNotIn("_auth_user_id", self.client.session)  # La sesión no tiene usuario autenticado
