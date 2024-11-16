from django.urls import path, include
from . import views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('', views.home, name='home'),
    path('reservar/<int:propiedad_id>/', views.crear_reserva, name='crear_reserva'),
    path('buscar/', views.buscar_alojamientos, name='buscar_alojamientos'),
    path('gestionPropiedad/', views.crear_propiedad, name='crear_propiedad'),
    path('historialReservas/', views.historial_reservas, name='historial_reservas'),
]
