from django.test import TestCase
from usuarios.models import PerfilUsuario
from django.contrib.auth.models import User

# Create your tests here.
class UsuarioModelTest(TestCase):
    def test_crear_usuario(self):
        perfil = PerfilUsuario.objects.create(
            usuario= User.objects.create_user(username='testuser', password='testpassword'),
            tipo_usuario='inquilino',
            telefono='1234567890'
        )
        self.assertEqual(perfil.usuario.username, "testuser")
        self.assertTrue(perfil.tipo_usuario, "inquilino")
        self.assertEqual(perfil.telefono, "1234567890")