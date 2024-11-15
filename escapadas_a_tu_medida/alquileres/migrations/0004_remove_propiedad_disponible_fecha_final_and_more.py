# Generated by Django 5.1.3 on 2024-11-15 18:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("alquileres", "0003_remove_propiedad_disponible_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="propiedad",
            name="disponible_fecha_final",
        ),
        migrations.RemoveField(
            model_name="propiedad",
            name="disponible_fecha_inicio",
        ),
        migrations.CreateModel(
            name="Disponibilidad",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("fecha", models.DateField()),
                (
                    "propiedad",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="disponibilidades",
                        to="alquileres.propiedad",
                    ),
                ),
            ],
            options={
                "unique_together": {("propiedad", "fecha")},
            },
        ),
    ]
