
from django import forms
from django.forms import inlineformset_factory
from .models import Propiedad, Imagen

class ImagenForm(forms.ModelForm):
    class Meta:
        model = Imagen
        fields = ['imagen', 'descripcion']

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
        fields = ['titulo', 'descripcion', 'ubicacion', 'precio_por_noche', 'disponible']

