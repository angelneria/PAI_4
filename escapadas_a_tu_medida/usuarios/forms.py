# usuarios/forms.py

from django import forms
from django.contrib.auth.models import User
from .models import PerfilUsuario
from django.contrib.auth.forms import AuthenticationForm
import re


class FormularioRegistroUsuario(forms.ModelForm):
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    confirmar_password = forms.CharField(label="Confirmar Contraseña", widget=forms.PasswordInput)
    tipo_usuario = forms.ChoiceField(choices=PerfilUsuario.USUARIO_TIPO_CHOICES, label="Tipo de usuario")
    telefono = forms.CharField(label="Telefono", max_length=15)
    first_name = forms.CharField(label="Nombre")
    last_name = forms.CharField(label="Apellidos")
    email = forms.EmailField(label="Correo",required=True)
    class Meta:
        model = User
        fields = ['username', 'email','first_name','last_name','password' ]
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
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está en uso.")
        return email
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if PerfilUsuario.objects.filter(telefono=telefono).exists():
            raise forms.ValidationError("Este número de teléfono ya está en uso.")
        return telefono

    def clean_password(self):
        password = self.cleaned_data.get("password")
        username = self.cleaned_data.get("username")
        if password == username:
            raise forms.ValidationError("La contraseña no puede ser igual al nombre de usuario")
        
        if len(password) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres")
        
        if not re.search(r'[a-zA-Z]',password):
            raise forms.ValidationError("La contraseña debe tener al 1 letra")
        
        return password        



class FormularioInicioSesion(AuthenticationForm):
    username = forms.CharField(label="Usuario", max_length=255)
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)


class FormularioEdicionUsuario(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']  # Campos editables
        widgets = {
            'email': forms.EmailInput(attrs={'id': 'id_email'}),
        }
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo',
            'first_name': 'Nombre',
            'last_name': 'Apellidos',
        }
        help_texts = {
            'username': None,
        }
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email != self.instance.email:
            if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Este correo electrónico ya está en uso.")
        return email


class FormularioEdicionPerfilUsuario(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ['telefono']  # Campos editables del perfil
        labels = {
            'telefono': 'Teléfono',
        }
        widgets = {
            'telefono': forms.TextInput(attrs={'placeholder': 'Ingrese su número de teléfono'}),
        }
