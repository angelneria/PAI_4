# usuarios/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .forms import FormularioRegistroUsuario, FormularioInicioSesion
from .models import PerfilUsuario
from django.contrib.auth.models import User

def registro(request):
    if request.method == "POST":
        form = FormularioRegistroUsuario(request.POST)
        if form.is_valid():
            # Crear el usuario
            usuario = form.save(commit=False)
            usuario.set_password(form.cleaned_data["password"])
            usuario.save()
            
            # Crear el perfil adicional
            tipo_usuario = form.cleaned_data.get("tipo_usuario")
            PerfilUsuario.objects.create(usuario=usuario, tipo_usuario=tipo_usuario)
            
            # Iniciar sesión automáticamente después de registrarse
            login(request, usuario)
            messages.success(request, "Registro exitoso. ¡Bienvenido!")
            # Redirige a la página inicial según el tipo de usuario
            return redirect("listar_propiedades")
    else:
        form = FormularioRegistroUsuario()
    
    return render(request, "usuarios/registro.html", {"form": form})


def iniciar_sesion(request):
    if request.method == "POST":
        form = FormularioInicioSesion(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                perfil = user.perfilusuario  # obtenemos el perfil de usuario
                if perfil.es_inquilino():
                    return redirect('/')  # redirige a la vista de inquilinos
                elif perfil.es_anfitrion():
                    return redirect('/')  # redirige a la vista de anfitriones
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    else:
        form = FormularioInicioSesion()
    return render(request, "usuarios/iniciar_sesion.html", {"form": form})

