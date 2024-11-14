from django.contrib import admin
from alquileres.models import Imagen, Propiedad, Reserva


admin.site.register(Reserva)
admin.site.register(Imagen)
admin.site.register(Propiedad)

# Register your models here.
