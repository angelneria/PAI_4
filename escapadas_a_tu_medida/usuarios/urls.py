# usuarios/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.iniciar_sesion, name='iniciar_sesion'),
    path('registro/', views.registro, name='registro'),  # URL para el registro
]
