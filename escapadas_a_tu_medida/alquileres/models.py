# alquileres/models.py

import datetime
from django.db import models
from django.forms import ValidationError
from usuarios.models import PerfilUsuario
from django.utils.timezone import now

# models.py
from django.db import models

class Propiedad(models.Model):
    propietario = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE, limit_choices_to={'tipo_usuario': 'anfitrion'})
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    ubicacion = models.CharField(max_length=255)
    precio_por_noche = models.DecimalField(max_digits=10, decimal_places=2)
    num_maximo_huespedes = models.IntegerField()
    num_maximo_habitaciones = models.IntegerField()
    servicios_disponibles = models.TextField()


    def __str__(self):
        return self.titulo
    

    def clean(self):
        super().clean()

        if self.precio_por_noche <= 0:
            raise ValidationError("El valor debe ser positivo")


    
        if self.pk and not self.imagenes.exists():
            raise ValidationError("Cada propiedad debe tener al menos una imagen asociada.")

        # Validación de fechas en disponibilidades
        if self.pk:
            fechas_invalidas = self.disponibilidades.filter(fecha__lt=now().date())
            if fechas_invalidas.exists():
                raise ValidationError("La propiedad tiene fechas de disponibilidad anteriores a la actual.")
    
class Disponibilidad(models.Model):
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='disponibilidades')
    fecha = models.DateField()

    class Meta:
        unique_together = ('propiedad', 'fecha')  # Asegura que no haya duplicados

    def __str__(self):
        return f"{self.propiedad.titulo} - {self.fecha}"
    
    def clean(self):
        super.clean()
        
        # Validación: La fecha no debe ser anterior a la actual
        if self.fecha < now().date():
            raise ValidationError("La fecha de disponibilidad no puede ser anterior a la fecha actual.")

    

class Imagen(models.Model):
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='imagenes')  # Relación de muchas a uno con Propiedad
    imagen = models.ImageField(upload_to='propiedades/', blank=True)  # Campo para la imagen
    
    def __str__(self):
        return f"Imagen de {self.propiedad.titulo}"




class Reserva(models.Model):
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE)
    inquilino = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE, limit_choices_to={'tipo_usuario': 'inquilino'})
    numero_huespedes = models.IntegerField()
    fechas_reserva = models.JSONField(default=list)  # Almacena las fechas reservadas como una lista
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Validar que se seleccionaron fechas
        if not self.fechas_reserva:
            raise ValidationError("Debe seleccionar al menos una fecha para la reserva.")

        # Verificar que las fechas están disponibles para la propiedad
        fechas_seleccionadas = set(self.fechas_reserva)
        disponibilidades = Disponibilidad.objects.filter(
            propiedad=self.propiedad,
            fecha__in=fechas_seleccionadas
        )

        if disponibilidades.count() != len(fechas_seleccionadas):
            raise ValidationError("Una o más fechas seleccionadas no están disponibles.")

        # Eliminar las fechas de la tabla de Disponibilidad
        disponibilidades.delete()

        # Calcular el total si no está definido
        if not self.total:
            self.total = len(fechas_seleccionadas) * self.propiedad.precio_por_noche

        super().save(*args, **kwargs)

    def __str__(self):
        fechas = ", ".join(self.fechas_reserva)
        return f"Reserva de {self.inquilino} para {self.propiedad} en las fechas: {fechas}"


class PropiedadesDeseadas(models.Model):
    inquilino = models.ManyToManyField(PerfilUsuario, related_name='propiedades_deseadas')
    propiedad = models.ManyToManyField(Propiedad, related_name='propiedades_deseadas')


    def str(self):
        return f"{', '.join([str(p) for p in self.propiedad.all()])} - {', '.join([i.usuario.nombre for i in self.inquilino.all()])}"
