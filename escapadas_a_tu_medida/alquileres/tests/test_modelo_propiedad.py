from django.forms import ValidationError
from django.test import TestCase
from usuarios.models import PerfilUsuario
from django.contrib.auth.models import User
from alquileres.models import Propiedad, Disponibilidad, Imagen
from django.utils.timezone import now, timedelta

# Create your tests here.
class PropiedadModelTest(TestCase):
    def test_crear_propiedad(self):
        propietario = PerfilUsuario.objects.create(
            usuario= User.objects.create_user(username='testuser', password='testpassword'),
            tipo_usuario='anfitrion',
            telefono='1234567890'
        )

        propiedad = Propiedad.objects.create(
            propietario=propietario,
            titulo='Test Propiedad',
            descripcion='Test Descripcion',
            ubicacion='Test Ubicacion',
            precio_por_noche=100.00,
            num_maximo_huespedes=2,
            num_maximo_habitaciones=1,
            tipo = 'apartamento',
            servicios_disponibles='Test Servicios'
        )

        self.assertEqual(propietario.usuario.username, "testuser")
        self.assertTrue(propietario.tipo_usuario, "anfitrion")
        self.assertEqual(propietario.telefono, "1234567890")

        self.assertEqual(propiedad.propietario, propietario)
        self.assertEqual(propiedad.titulo, "Test Propiedad")
        self.assertEqual(propiedad.descripcion, "Test Descripcion")
        self.assertEqual(propiedad.ubicacion, "Test Ubicacion")
        self.assertEqual(propiedad.precio_por_noche, 100.00)    
        self.assertEqual(propiedad.num_maximo_huespedes, 2)
        self.assertEqual(propiedad.num_maximo_habitaciones, 1)
        self.assertEqual(propiedad.servicios_disponibles, "Test Servicios")
        self.assertEqual(propiedad.tipo, "apartamento")



    def test_validacion_precio_positivo(self):
        propietario = PerfilUsuario.objects.create(
            usuario= User.objects.create_user(username='testuser', password='testpassword'),
            tipo_usuario='anfitrion',
            telefono='1234567890'
        )

        propiedad1 = Propiedad.objects.create(
            propietario=propietario,
            titulo='Test Propiedad',
            descripcion='Test Descripcion',
            ubicacion='Test Ubicacion',
            precio_por_noche=-100.00,
            num_maximo_huespedes=2,
            num_maximo_habitaciones=1,
            servicios_disponibles='Test Servicios'
        )

        with self.assertRaises(ValidationError) as e:
            propiedad1.full_clean()  # Esto ejecuta las validaciones del modelo
        self.assertIn("El valor debe ser positivo", str(e.exception))
    

    def test_validacion_una_imagen(self):
        propietario = PerfilUsuario.objects.create(
            usuario= User.objects.create_user(username='testuser', password='testpassword'),
            tipo_usuario='anfitrion',
            telefono='1234567890'
        )

        propiedad2 = Propiedad.objects.create(
            propietario=propietario,
            titulo='Test Propiedad',
            descripcion='Test Descripcion',
            ubicacion='Test Ubicacion',
            precio_por_noche=100.00,
            num_maximo_huespedes=2,
            num_maximo_habitaciones=1,
            servicios_disponibles='Test Servicios'
        )

        with self.assertRaises(ValidationError) as e:
            propiedad2.full_clean()
        self.assertIn("Cada propiedad debe tener al menos una imagen asociada.", str(e.exception))

    def test_propiedad_con_fechas_de_disponibilidad_invalidas(self):
        propietario = PerfilUsuario.objects.create(
            usuario= User.objects.create_user(username='testuser', password='testpassword'),
            tipo_usuario='anfitrion',
            telefono='1234567890'
        )
        propiedad3 = Propiedad.objects.create(propietario=propietario,
            titulo='Test Propiedad con fechas invalidas',
            descripcion='Test Descripcion',
            ubicacion='Test Ubicacion',
            precio_por_noche=100.00,
            num_maximo_huespedes=2,
            num_maximo_habitaciones=1,
            servicios_disponibles='Test Servicios'
        )
        Imagen.objects.create(propiedad=propiedad3, imagen='escapadas_a_tu_medida/media/navbar.jpg')
        fecha_pasada = now().date() - timedelta(days=10)
        Disponibilidad.objects.create(fecha=fecha_pasada, propiedad=propiedad3)
        

        with self.assertRaises(ValidationError) as e:
            propiedad3.full_clean()
        self.assertIn("La propiedad tiene fechas de disponibilidad anteriores a la actual.", str(e.exception))




    def test_tipo_propiedad_valida(self):
            
            propietario = PerfilUsuario.objects.create(
                usuario= User.objects.create_user(username='testuser', password='testpassword'),
                tipo_usuario='anfitrion',
                telefono='1234567890'
            )


            # Crear una propiedad con un tipo válido
            propiedad = Propiedad(
                propietario=propietario,
                titulo="Propiedad de prueba",
                descripcion="Descripción de prueba",
                ubicacion="Ubicación de prueba",
                precio_por_noche=100.00,
                num_maximo_huespedes=4,
                num_maximo_habitaciones=2,
                servicios_disponibles="Wifi, Piscina",
                tipo="apartamento"  # Tipo válido
            )
            try:
                propiedad.full_clean()  # Validar los datos del modelo
                propiedad.save()
            except ValidationError:
                self.fail("La propiedad con tipo válido no debería generar un error")

            # Verificar que la propiedad se guardó correctamente
            self.assertEqual(Propiedad.objects.count(), 1)
            self.assertEqual(Propiedad.objects.first().tipo, "apartamento")

    def test_tipo_propiedad_invalido(self):
            # Crear una propiedad con un tipo no válido

            propietario = PerfilUsuario.objects.create(
                usuario= User.objects.create_user(username='testuser', password='testpassword'),
                tipo_usuario='anfitrion',
                telefono='1234567890'
            )


            propiedad = Propiedad(
                propietario=propietario,
                titulo="Propiedad de prueba",
                descripcion="Descripción de prueba",
                ubicacion="Ubicación de prueba",
                precio_por_noche=100.00,
                num_maximo_huespedes=4,
                num_maximo_habitaciones=2,
                servicios_disponibles="Wifi, Piscina",
                tipo="casa_flotante_invalida"  # Tipo no válido
            )
            with self.assertRaises(ValidationError):
                propiedad.full_clean()  # Esto debería lanzar un ValidationError
