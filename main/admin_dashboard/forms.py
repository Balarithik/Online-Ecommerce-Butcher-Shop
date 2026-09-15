from django import forms
from django.core.validators import validate_image_file_extension
from store.models import Products

class ProductForm(forms.ModelForm):
    class Meta:
        model = Products
        fields = ['name', 'price', 'description', 'is_available', 'image1', 'image2', 'image3', 'image4']

    def clean(self):
        cleaned_data = super().clean()
        for field_name in ('image1', 'image2', 'image3', 'image4'):
            image = cleaned_data.get(field_name)
            if image:
                validate_image_file_extension(image)
                if image.size > 5 * 1024 * 1024:
                    self.add_error(field_name, 'Image files must be 5 MB or smaller.')
        return cleaned_data
