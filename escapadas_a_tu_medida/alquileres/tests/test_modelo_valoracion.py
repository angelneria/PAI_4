from django.test import TestCase
from django.core.exceptions import ValidationError
from alquileres.models import Propiedad, PerfilUsuario, Valoracion
from django.contrib.auth.models import User

class ValoracionModelTest(TestCase):

    def setUp(self):
        # Crear usuarios y propiedades de prueba

        self.usuario_1 = User.objects.create_user(
            username="usuario1",
            password="password123"
        )
        self.perfil_usuario1 = PerfilUsuario.objects.create(
            usuario=self.usuario_1,
            tipo_usuario="anfitrion"
        )

        self.usuario_2 = User.objects.create_user(
            username="usuario2",
            password="password123"
        )
        self.perfil_usuario2 = PerfilUsuario.objects.create(
            usuario=self.usuario_2,
            tipo_usuario="inquilino"
        )




        self.propiedad = Propiedad.objects.create(
            propietario=self.perfil_usuario1,
            titulo='Test Propiedad',
            descripcion='Test Descripcion',
            ubicacion='Test Ubicacion',
            precio_por_noche=100.00,
            num_maximo_huespedes=2,
            num_maximo_habitaciones=1,
            servicios_disponibles='Test Servicios'
        )

    def test_crear_valoracion_valida(self):
        # Crear una valoración válida
        valoracion = Valoracion(propiedad=self.propiedad, usuario=self.perfil_usuario2, calificacion=4)
        try:
            valoracion.clean()
            valoracion.save()
        except ValidationError:
            self.fail("La valoración válida no debería generar un error")
        # Verificar que la valoración se haya guardado correctamente
        self.assertEqual(Valoracion.objects.count(), 1)

    def test_calificacion_fuera_de_rango(self):
        # Crear una valoración con calificación fuera de rango (menos de 1)
        valoracion = Valoracion(propiedad=self.propiedad, usuario=self.perfil_usuario2, calificacion=0)
        with self.assertRaises(ValidationError):
            valoracion.clean()

        # Crear una valoración con calificación fuera de rango (más de 5)
        valoracion = Valoracion(propiedad=self.propiedad, usuario=self.perfil_usuario2, calificacion=6)
        with self.assertRaises(ValidationError):
            valoracion.clean()

    def test_un_usuario_una_valoracion_por_propiedad(self):
        # Crear una valoración por el mismo usuario para la misma propiedad
        valoracion1 = Valoracion(propiedad=self.propiedad, usuario=self.perfil_usuario2, calificacion=4)
        valoracion1.save()

        # Intentar crear una segunda valoración para la misma propiedad y usuario
        valoracion2 = Valoracion(propiedad=self.propiedad, usuario=self.perfil_usuario2, calificacion=5)
        
        # Usar full_clean() para validar las restricciones del modelo antes de guardar
        with self.assertRaises(ValidationError):
            valoracion2.full_clean()  # Esto lanzará el ValidationError si hay violación de unique_together
            valoracion2.save()


            


    def test_unique_together_constraint(self):
        # Comprobar que se respeta la restricción unique_together en la base de datos
        valoracion1 = Valoracion(propiedad=self.propiedad, usuario=self.perfil_usuario2, calificacion=4)
        valoracion1.save()

        # Verificar que no se pueda crear una segunda valoración para la misma propiedad y usuario
        with self.assertRaises(Exception):  # Este error se produce en la base de datos
            Valoracion.objects.create(propiedad=self.propiedad, usuario=self.perfil_usuario2, calificacion=5)
