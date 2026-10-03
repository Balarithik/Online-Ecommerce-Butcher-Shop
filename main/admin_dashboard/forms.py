from django import forms
from django.core.exceptions import ValidationError
import re
from store.models import Products


def validate_cloudinary_public_id(value):
    if not value:
        return

    if (
        not value.startswith('products_images/')
        or '//' in value
        or any(part in {'', '.', '..'} for part in value.split('/')[1:])
        or not re.fullmatch(r'[A-Za-z0-9_./-]+', value)
    ):
        raise ValidationError('Select a valid image uploaded to the product-images folder.')


class CloudinaryProductForm(forms.ModelForm):
    image1_public_id = forms.CharField(
        max_length=100,
        validators=[validate_cloudinary_public_id],
    )
    image2_public_id = forms.CharField(
        max_length=100,
        required=False,
        validators=[validate_cloudinary_public_id],
    )
    image3_public_id = forms.CharField(
        max_length=100,
        required=False,
        validators=[validate_cloudinary_public_id],
    )
    image4_public_id = forms.CharField(
        max_length=100,
        required=False,
        validators=[validate_cloudinary_public_id],
    )

    class Meta:
        model = Products
        fields = ['name', 'price', 'description', 'is_available']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and not self.is_bound:
            for number in range(1, 5):
                image = getattr(self.instance, f'image{number}')
                self.initial[f'image{number}_public_id'] = image.name
