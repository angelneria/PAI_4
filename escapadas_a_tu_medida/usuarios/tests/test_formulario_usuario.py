from django.test import TestCase
from usuarios.forms import (
    FormularioRegistroUsuario,
    FormularioInicioSesion,
    FormularioEdicionUsuario,
    FormularioEdicionPerfilUsuario,
)
from usuarios.models import PerfilUsuario
from django.contrib.auth.models import User


class TestFormularioRegistroUsuario(TestCase):
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

    def test_formulario_valido_registro(self):
        form = FormularioRegistroUsuario(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_passwords_no_coinciden(self):
        data = self.valid_data.copy()
        data["confirmar_password"] = "OtraPassword"
        form = FormularioRegistroUsuario(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("Las contraseñas no coinciden.", form.errors["confirmar_password"])

    def test_email_duplicado(self):
        User.objects.create_user(username="usuario2", email="usuario1@example.com", password="Password123!")
        form = FormularioRegistroUsuario(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn("Este correo electrónico ya está en uso.", form.errors["email"])

    def test_telefono_duplicado(self):
        PerfilUsuario.objects.create(usuario=User.objects.create(username="usuario3"), telefono="123456789")
        form = FormularioRegistroUsuario(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn("Este número de teléfono ya está en uso.", form.errors["telefono"])

    def test_password_invalida(self):
        data = self.valid_data.copy()
        data["password"] = "123"  # Muy corta
        form = FormularioRegistroUsuario(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("La contraseña debe tener al menos 8 caracteres", form.errors["password"])


class TestFormularioInicioSesion(TestCase):
    def setUp(self):
        # Crear usuario para las pruebas
        self.user = User.objects.create_user(
            username="usuario_prueba",
            password="Password123!"
        )

    def test_formulario_valido_inicio_sesion(self):
        # Datos correctos
        form_data = {
            "username": "usuario_prueba",
            "password": "Password123!"
        }
        form = FormularioInicioSesion(data=form_data)
        self.assertTrue(form.is_valid()) 


class TestFormularioEdicionUsuario(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="usuario", email="usuario@example.com", password="Password123!")

    def test_editar_email_valido(self):
        form = FormularioEdicionUsuario(instance=self.user, data={
            "username": self.user.username,
            "email": "nuevo@example.com",
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
        })
        self.assertTrue(form.is_valid())

    def test_editar_email_invalido(self):
        form = FormularioEdicionUsuario(instance=self.user, data={"email": "correo-invalido"})
        self.assertFalse(form.is_valid())
        self.assertIn("Introduzca una dirección de correo electrónico válida.", form.errors["email"])
                      
class TestFormularioEdicionPerfilUsuario(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="usuario", email="usuario@example.com", password="Password123!")
        self.perfil = PerfilUsuario.objects.create(usuario=user, telefono="123456789")

    def test_editar_telefono_valido(self):
        form = FormularioEdicionPerfilUsuario(instance=self.perfil, data={"telefono": "987654321"})
        self.assertTrue(form.is_valid())



