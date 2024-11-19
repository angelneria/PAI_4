# usuarios/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy


urlpatterns = [
    path('login/', views.iniciar_sesion, name='iniciar_sesion'),
    path('registro/', views.registro, name='registro'), # URL para el registro
    path('perfil/', views.editar_perfil, name='editar_perfil'), 
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='usuarios/contraseña/password_reset_form.html',
            email_template_name='usuarios/contraseña/password_reset_email.html',
            success_url=reverse_lazy('password_reset_done')), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='usuarios/contraseña/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='usuarios/contraseña/password_reset_confirm.html',
             post_reset_login=True), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='usuarios/contraseña/password_reset_complete.html',
            extra_context={'editar_url': reverse_lazy('editar_perfil')}), name='password_reset_complete'), 
    path('logout/', views.logout_view, name='logout'),
    path('chat/', views.lista_chats, name='lista_chats'),
    path('chat/', views.chat_view, name='chat'),
    path('chat/<str:room_name>/messages/', views.get_messages, name='get_messages'),
    path('chat/<str:room_name>/send/', views.send_message, name='send_message'),
]
