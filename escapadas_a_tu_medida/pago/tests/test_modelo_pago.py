from django.test import TestCase
from django.contrib.auth.models import User
from pago.models import Payment
from django.db.utils import IntegrityError



class PaymentModelTest(TestCase):

    def setUp(self):
        # Crear un usuario de prueba
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_create_payment(self):
        # Crear un pago válido
        payment = Payment(
            user=self.user,
            amount=100.50,
            payment_intent="pi_1Gv1w2A8P0fGVh71W3UJ3bTH",  # Ejemplo de intent de pago
            status="pending"
        )
        payment.save()

        # Verificar que el pago se ha guardado correctamente
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.amount, 100.50)
        self.assertEqual(payment.payment_intent, "pi_1Gv1w2A8P0fGVh71W3UJ3bTH")
        self.assertEqual(payment.status, "pending")

    def test_payment_intent_unique(self):
        # Crear un primer pago con un payment_intent
        Payment.objects.create(
            user=self.user,
            amount=100.50,
            payment_intent="pi_1Gv1w2A8P0fGVh71W3UJ3bTH",
            status="pending"
        )

        # Intentar crear un segundo pago con el mismo payment_intent
        with self.assertRaises(IntegrityError):
            Payment.objects.create(
                user=self.user,
                amount=50.00,
                payment_intent="pi_1Gv1w2A8P0fGVh71W3UJ3bTH",  # Mismo payment_intent
                status="pending"
            )

    def test_default_status(self):
        # Crear un pago sin especificar el status
        payment = Payment.objects.create(
            user=self.user,
            amount=100.50,
            payment_intent="pi_1Gv1w2A8P0fGVh71W3UJ3bTH"
        )

        # Verificar que el status por defecto sea "pending"
        self.assertEqual(payment.status, "pending")

    def test_status_update(self):
        # Crear un pago con status "pending"
        payment = Payment.objects.create(
            user=self.user,
            amount=100.50,
            payment_intent="pi_1Gv1w2A8P0fGVh71W3UJ3bTH",
            status="pending"
        )

        # Cambiar el status del pago a "completed"
        payment.status = "completed"
        payment.save()

        # Verificar que el status ha sido actualizado correctamente
        self.assertEqual(payment.status, "completed")

    def test_created_at_auto_now_add(self):
        # Crear un pago y verificar la fecha de creación
        payment = Payment.objects.create(
            user=self.user,
            amount=100.50,
            payment_intent="pi_1Gv1w2A8P0fGVh71W3UJ3bTH"
        )

        # Verificar que la fecha de creación no sea None
        self.assertIsNotNone(payment.created_at)
