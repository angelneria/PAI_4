
# usuarios/models.py

from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now


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
    
class Message(models.Model):
    room = models.CharField(max_length=255)
    sender = models.CharField(max_length=255)
    content = models.TextField()
    timestamp = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"

    class Meta:
        ordering = ('timestamp',)

