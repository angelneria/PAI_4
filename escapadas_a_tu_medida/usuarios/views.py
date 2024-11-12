# usuarios/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .forms import FormularioEdicionPerfil, FormularioRegistroUsuario, FormularioInicioSesion
from .models import PerfilUsuario
from django.urls import reverse
from django.contrib.auth.decorators import login_required

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
            return redirect("/")
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

@login_required
def editar_perfil(request):
    user = request.user  # Usuario actual
    if request.method == "POST":
        form = FormularioEdicionPerfil(request.POST, instance=user)
        if form.is_valid():
            form.save()  # Guardamos solo username y email
            messages.success(request, "Perfil actualizado exitosamente.")
            return redirect('/')  # Cambia al nombre de la vista a la que quieras redirigir
        else:
            messages.error(request, "Hubo un error al actualizar el perfil.")
    else:
        form = FormularioEdicionPerfil(instance=user)

    # Generamos la URL para el restablecimiento de contraseña
    cambio_contrasena_url = reverse('password_reset')  # Nombre de la vista para cambiar contraseña

    return render(request, "usuarios/perfil.html", {
        "form": form,
        "cambio_contrasena_url": cambio_contrasena_url,
    })


def logout_view(request):
    logout(request)  # Esto cierra solo la sesión del usuario actual
    return redirect('/')  # Redirige a la página principal u otra URL que prefieras

