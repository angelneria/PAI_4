from django.http import HttpResponseForbidden
from django.shortcuts import redirect
import re


class RestringirRutasMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Configura las rutas que quieres proteger
        self.rutas_protegidas = {
            '^/gestionPropiedad/create$': 'anfitrion',
            '^/reservar/\d+/$': 'inquilino',
            '^/confirmar_reserva/\d+/$': 'inquilino',
            '^/gestionPropiedad/delete/\d+/$': 'anfitrion',
            '^/gestionPropiedad/update/\d+/$': 'anfitrion',
            '^/historialReservas': 'anfitrion',
            '^/seguimientoReservas/\d+/$': 'inquilino',
            '^/agregarListaDeseos/\d+/$': 'inquilino',
            '^/eliminarListaDeseos/\d+/$': 'inquilino',
            '^/listaDeseos': 'inquilino',
            '^/valorarPropiedad/\d+/$': 'inquilino',

        }

        self.rutas_no_autenticado = ['/reservar','/seguimientoReservas']

    def __call__(self, request):
        # Lógica de restricción
        ruta = request.path

        if request.user.is_authenticated:
            perfil_usuario = request.user.perfilusuario
            rol = perfil_usuario.tipo_usuario  # Solo lo obtenemos si el usuario está autenticado
            for patron, rol_requerido in self.rutas_protegidas.items():
                if re.match(patron, ruta):  # Compara la ruta con el patrón usando expresiones regulares
                    if rol != rol_requerido:
                        return HttpResponseForbidden(f"Acceso restringido a {rol}.")
                        

        else:
            if not ruta in self.rutas_no_autenticado:
                        for patron in self.rutas_protegidas.keys():
                            if re.match(patron, ruta):
                                return redirect('/login')  # Si no está autenticado, no intentamos obtener el perfil 


                



        return self.get_response(request)


        


        