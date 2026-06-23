from django import forms
from store.models import Products

class ProductForm(forms.ModelForm):
    class Meta:
        model = Products
        fields = ['name', 'price', 'description', 'image1', 'image2', 'image3', 'image4']
