# usuarios/forms.py

from django import forms
from django.contrib.auth.models import User
from .models import PerfilUsuario
from django.contrib.auth.forms import AuthenticationForm

class FormularioRegistroUsuario(forms.ModelForm):
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    confirmar_password = forms.CharField(label="Confirmar Contraseña", widget=forms.PasswordInput)
    tipo_usuario = forms.ChoiceField(choices=PerfilUsuario.USUARIO_TIPO_CHOICES, label="Tipo de usuario")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        labels = {
            'email': 'Correo', 
            'username': 'Nombre de usuario', # Cambia la etiqueta del campo "email" a "Correo"
        }

    def clean_confirmar_password(self):
        password = self.cleaned_data.get("password")
        confirmar_password = self.cleaned_data.get("confirmar_password")
        if password != confirmar_password:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return confirmar_password

class FormularioInicioSesion(AuthenticationForm):
    username = forms.CharField(label="Usuario", max_length=255)
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
