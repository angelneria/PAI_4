# Generated by Django 5.1.3 on 2024-11-23 10:54

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("alquileres", "0009_reserva_email_cliente_reserva_nombre_cliente_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="reserva",
            old_name="email_cliente",
            new_name="correo_usuario_anonimo",
        ),
        migrations.RenameField(
            model_name="reserva",
            old_name="nombre_cliente",
            new_name="nombre_usuario_anonimo",
        ),
        migrations.RenameField(
            model_name="reserva",
            old_name="telefono_cliente",
            new_name="telefono_usuario_anonimo",
        ),
    ]
