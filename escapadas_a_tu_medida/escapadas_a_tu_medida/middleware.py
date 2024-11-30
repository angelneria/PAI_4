from django.http import HttpResponseForbidden
from django.shortcuts import redirect
import re


class RestringirRutasMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Configura las rutas que quieres proteger
        self.rutas_protegidas = {
            '^/gestionPropiedad/create$': ['anfitrion'],
            '^/reservar/\d+/$': ['inquilino'],
            '^/confirmar_reserva/\d+/$': ['inquilino'],
            '^/gestionPropiedad/delete/\d+/$': ['anfitrion'],
            '^/gestionPropiedad/update/\d+/$': ['anfitrion'],
            '^/historialReservas': ['anfitrion'],
            '^/seguimientoReservas/\d+/$': ['inquilino'],
            '^/agregarListaDeseos/\d+/$': ['inquilino'],
            '^/eliminarListaDeseos/\d+/$': ['inquilino'],
            '^/listaDeseos': ['inquilino'],
            '^/valorarPropiedad/\d+/$': ['inquilino'],
            '^/pagoRealizado': ['inquilino'],
            '^/pago': ['inquilino'],
            '^/perfil': ['inquilino', 'anfitrion'],
            '^/password_reset': ['inquilino', 'anfitrion'],
            '^/reset': ['inquilino', 'anfitrion'],
            '^/chat': ['inquilino', 'anfitrion'],





        }

        self.rutas_no_autenticado = ['/reservar','/seguimientoReservas', '/confirmar_reserva','/pagoRealizado','/pago' ]

    def __call__(self, request):
        # Lógica de restricción
        ruta = request.path

        if request.user.is_authenticated:
            perfil_usuario = request.user.perfilusuario
            rol = perfil_usuario.tipo_usuario  # Solo lo obtenemos si el usuario está autenticado
            for patron, rol_requerido in self.rutas_protegidas.items():
                if re.match(patron, ruta):  # Compara la ruta con el patrón usando expresiones regulares
                    if rol not in rol_requerido: 
                        return HttpResponseForbidden(f"Acceso restringido a {rol}.")
        else:
            # Si el usuario no está autenticado
            # Verificar si la ruta está en rutas_no_autenticado
            permitido = any(re.match(patron_no_autenticado, ruta) for patron_no_autenticado in self.rutas_no_autenticado)
            if not permitido:
                # Si no está en rutas_no_autenticado, verificar si está en rutas protegidas
                protegido = any(re.match(patron, ruta) for patron in self.rutas_protegidas)
                if protegido:
                    return redirect('/login')

        return self.get_response(request)



                



        


        