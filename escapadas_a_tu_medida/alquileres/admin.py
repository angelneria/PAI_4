from django.contrib import admin
from alquileres.models import Imagen, Propiedad, Reserva, Disponibilidad, PropiedadesDeseadas, Valoracion


admin.site.register(Reserva)
admin.site.register(Imagen)
admin.site.register(Propiedad)
admin.site.register(Disponibilidad)
admin.site.register(PropiedadesDeseadas)
admin.site.register(Valoracion)

# Register your models here.
