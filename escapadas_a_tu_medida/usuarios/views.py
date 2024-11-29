# usuarios/views.py

import json
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.urls import reverse
from .forms import FormularioEdicionPerfilUsuario, FormularioEdicionUsuario, FormularioRegistroUsuario, FormularioInicioSesion
from .models import PerfilUsuario, User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from .models import Message
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404



def registro(request):
    if request.method == "POST":
        form = FormularioRegistroUsuario(request.POST)
        if form.is_valid():
            # Crear el usuario
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            
            user = get_user_model().objects.create_user(
                username=username, 
                email=email, 
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Crear el perfil adicional
            tipo_usuario = form.cleaned_data.get("tipo_usuario")
            telefono = form.cleaned_data.get("telefono")
            PerfilUsuario.objects.create(usuario=user, tipo_usuario=tipo_usuario, telefono=telefono)
            
            # Iniciar sesión automáticamente después de registrarse
            login(request, user)
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
    perfil = user.perfilusuario  # Relación OneToOne entre User y PerfilUsuario

    if request.method == "POST":
        form_user = FormularioEdicionUsuario(request.POST, instance=user)
        form_perfil = FormularioEdicionPerfilUsuario(request.POST, instance=perfil)

        if form_user.is_valid() and form_perfil.is_valid():
            form_user.save()
            form_perfil.save()
            messages.success(request, "Perfil actualizado exitosamente.")
            return redirect('/')  # Redirigir a la página deseada
        else:
            messages.error(request, "Hubo un error al actualizar el perfil.")
    else:
        form_user = FormularioEdicionUsuario(instance=user)
        form_perfil = FormularioEdicionPerfilUsuario(instance=perfil)

    cambio_contrasena_url = reverse('password_reset') + f"?email={user.email}"


    return render(request, "usuarios/perfil.html", {
        "form_user": form_user,
        "form_perfil": form_perfil,
        "cambio_contrasena_url": cambio_contrasena_url,
    })


def logout_view(request):
    logout(request)  # Esto cierra solo la sesión del usuario actual
    return redirect('/')  # Redirige a la página principal u otra URL que prefieras

def lista_chats(request):
    # Obtenemos el perfil del usuario logueado
    perfil_usuario = request.user.perfilusuario

    # Definir los contactos dependiendo del rol del usuario
    if perfil_usuario.tipo_usuario == "anfitrion":
        # Es un propietario: listar todos los inquilinos
        contactos = PerfilUsuario.objects.filter(tipo_usuario="inquilino")
        rol_contacto = "inquilino"
    elif perfil_usuario.tipo_usuario == "inquilino":
        # Es un inquilino: listar todos los propietarios
        contactos = PerfilUsuario.objects.filter(tipo_usuario="anfitrion")
        rol_contacto = "propietario"
    else:
        # Otros roles no tienen chats
        contactos = []
        rol_contacto = None

    # Generar las salas de chat para cada contacto
    chats = []
    for contacto in contactos:
        room_name = f'chat_{min(perfil_usuario.usuario.id, contacto.usuario.id)}_{max(perfil_usuario.usuario.id, contacto.usuario.id)}'
        
        # Obtener el último mensaje de la sala
        ultimo_mensaje = (
            Message.objects.filter(room=room_name)
            .order_by('-timestamp')
            .first()  # Obtener el mensaje más reciente
        )
        
        chats.append({
            'contacto': contacto,
            'room_name': room_name,
            'ultimo_mensaje': ultimo_mensaje.content if ultimo_mensaje else "No hay mensajes",
            'timestamp': ultimo_mensaje.timestamp.strftime("%Y-%m-%d %H:%M:%S") if ultimo_mensaje else "",
        })

    return render(request, 'usuarios/chat.html', {
        'chats': chats,
        'rol_contacto': rol_contacto,
        'perfil_usuario': perfil_usuario
    })

def chat_view(request, room_name):
    # Parsear el ID del usuario actual y del contacto desde el room_name
    try:
        user_id_1, user_id_2 = map(int, room_name.split('_')[1:])
    except ValueError:
        return render(request, 'usuarios/error.html', {'error': 'Sala de chat no válida'})

    # Identificar el contacto (el otro usuario en el chat)
    current_user_id = request.user.id
    contact_user_id = user_id_2 if current_user_id == user_id_1 else user_id_1

    # Obtener el perfil del contacto
    contacto = get_object_or_404(User, id=contact_user_id)



    return render(request, 'usuarios/chat.html', {
        'room_name': room_name,
        'contact_name': contacto.username,  # Pasar el nombre del contacto al template
    })

def get_messages(request, room_name):
    messages = Message.objects.filter(room=room_name)
    
    data = [
        {
            "sender": message.sender,
            "content": message.content,
            "timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for message in messages
    ]
    return JsonResponse({"messages": data})

@csrf_exempt
def send_message(request, room_name):
    if request.method == 'POST':
        data = json.loads(request.body)
        current_user = request.user

        message = Message.objects.create(
            room=room_name,
            sender=current_user.username,    
            content=data['content'],
        )
        return JsonResponse({
            "sender": message.sender,
            "content": message.content,
            "timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        })