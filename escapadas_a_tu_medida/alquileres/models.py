# alquileres/models.py

from django.db import models
from usuarios.models import PerfilUsuario

class Propiedad(models.Model):
    propietario = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE, limit_choices_to={'tipo_usuario': 'anfitrion'})
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    ubicacion = models.CharField(max_length=255)
    precio_por_noche = models.DecimalField(max_digits=10, decimal_places=2)
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return self.titulo

class Reserva(models.Model):
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE)
    inquilino = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE, limit_choices_to={'tipo_usuario': 'inquilino'})
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Calcula el total antes de guardar la reserva
        if not self.total:
            dias = (self.fecha_fin - self.fecha_inicio).days
            self.total = dias * self.propiedad.precio_por_noche
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reserva de {self.inquilino} para {self.propiedad}"

