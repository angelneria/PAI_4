from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('propiedades/', views.listar_propiedades, name='listar_propiedades'),
    path('propiedad/<int:propiedad_id>/reservar/', views.reservar_propiedad, name='reservar_propiedad'),
    path('buscar/', views.buscar, name='buscar'),
    path('buscar/filtros', views.buscar_alojamientos, name='buscar_alojamientos'),
    path('gestionPropiedad/', views.crear_propiedad, name='crear_propiedad'),
]
