from django.contrib import admin
from alquileres.models import Imagen, Propiedad, Reserva, Disponibilidad, PropiedadesDeseadas


admin.site.register(Reserva)
admin.site.register(Imagen)
admin.site.register(Propiedad)
admin.site.register(Disponibilidad)
admin.site.register(PropiedadesDeseadas)

# Register your models here.
