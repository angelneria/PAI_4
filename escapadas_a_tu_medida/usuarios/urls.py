# usuarios/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('login/', views.iniciar_sesion, name='iniciar_sesion'),
    path('registro/', views.registro, name='registro'),  # URL para el registro
    path('logout/', views.logout_view, name='logout'),
]
