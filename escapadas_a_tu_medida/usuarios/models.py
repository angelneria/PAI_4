
# usuarios/models.py

from django.contrib.auth.models import User
from django.db import models

class PerfilUsuario(models.Model):
    USUARIO_TIPO_CHOICES = [
        ('inquilino', 'Inquilino'),
        ('anfitrion', 'Anfitrión'),
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo_usuario = models.CharField(max_length=10, choices=USUARIO_TIPO_CHOICES)
    telefono = models.CharField(max_length=15, blank=True, null=True)

    def es_inquilino(self):
        return self.tipo_usuario == 'inquilino'
    
    def es_anfitrion(self):
        return self.tipo_usuario == 'anfitrion'
    
    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_usuario_display()}"

