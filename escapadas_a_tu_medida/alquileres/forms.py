
from django import forms
from django.forms import inlineformset_factory
from .models import Propiedad, Imagen, Reserva

class ImagenForm(forms.ModelForm):
    class Meta:
        model = Imagen
        fields = ['imagen']


# Crear un formset para las imágenes asociadas a una propiedad
ImagenFormSet = inlineformset_factory(
    Propiedad, Imagen,  # Relación entre propiedad e imagen
    form=ImagenForm,  # Formulario para cada imagen
    extra=10,  # Añade un formulario vacío inicialmente
    max_num=10,  # Límite de 10 imágenes
    can_delete=False  # Opción para eliminar imágenes
)

class PropiedadForm(forms.ModelForm):
    class Meta:
        model = Propiedad
        fields = ['titulo', 'descripcion', 'ubicacion', 'precio_por_noche', 'num_maximo_huespedes', 'num_maximo_habitaciones', 'servicios_disponibles']

class FiltroAlojamientosForm(forms.Form):
    query = forms.CharField()
    precio_min = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label="Precio mínimo")
    precio_max = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label="Precio máximo")

class FiltroAlojamientosHomeForm(forms.Form):
    precio_min = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label="Precio mínimo")
    precio_max = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label="Precio máximo")


class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['fecha_inicio', 'fecha_fin']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }