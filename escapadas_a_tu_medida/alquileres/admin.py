from django.contrib import admin
from alquileres.models import Imagen, Propiedad, Reserva, Disponibilidad


admin.site.register(Reserva)
admin.site.register(Imagen)
admin.site.register(Propiedad)
admin.site.register(Disponibilidad)

# Register your models here.
