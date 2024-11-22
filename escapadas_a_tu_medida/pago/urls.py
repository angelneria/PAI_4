from django.urls import path
from . import views

from django.conf import settings

urlpatterns = [
    path('pago/<int:propiedad_id>/<str:monto>/', views.procesar_pago, name='procesar_pago'),
    path('webhooks/stripe/', views.stripe_webhook, name='stripe_webhook'),
    
]
