# Generated by Django 5.1.3 on 2024-11-17 12:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("alquileres", "0006_remove_imagen_descripcion"),
        ("usuarios", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PropiedadesDeseadas",
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
                (
                    "inquilino",
                    models.ManyToManyField(
                        related_name="propiedades_deseadas", to="usuarios.perfilusuario"
                    ),
                ),
                (
                    "propiedad",
                    models.ManyToManyField(
                        related_name="propiedades_deseadas", to="alquileres.propiedad"
                    ),
                ),
            ],
        ),
    ]
