from django.shortcuts import get_object_or_404, render

import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from alquileres.models import Propiedad, Reserva

from .models import Payment
from django.contrib.auth.decorators import login_required

stripe.api_key = settings.STRIPE_SECRET_KEY

def procesar_pago(request, propiedad_id, monto):

    
    if request.method == 'POST':
        # Crear el PaymentIntent
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(float(monto) * 100),  
                currency='eur',
                payment_method_types=['card'],
            )
            return JsonResponse({'clientSecret': intent['client_secret']})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    propiedad = Propiedad.objects.get(pk=propiedad_id)
    return render(request, 'pago.html', {
        'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
        'monto': monto,
        'propiedad': propiedad
    })







