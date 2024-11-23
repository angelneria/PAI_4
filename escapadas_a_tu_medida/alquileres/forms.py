
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
    numero_huespedes = forms.IntegerField(initial=1)
    class Meta:
        model = Reserva
        fields = ['numero_huespedes']

    def __init__(self, *args, **kwargs):
        self.propiedad_id = kwargs.pop('propiedad_id', None)  # Extrae el id de la propiedad
        super().__init__(*args, **kwargs)

    def clean_numero_huespedes(self):
        n_huespedes = self.cleaned_data.get('numero_huespedes',0)
        
        # Asegúrate de que la propiedad existe
        try:
            propiedad = Propiedad.objects.get(id=self.propiedad_id)
        except Propiedad.DoesNotExist:
            raise forms.ValidationError("La propiedad no existe.")

        # Verifica si el número de huéspedes excede el máximo permitido
        if propiedad.num_maximo_huespedes < n_huespedes:
            raise forms.ValidationError("El número de huéspedes no puede ser mayor al permitido.")

        return n_huespedes
    



        

