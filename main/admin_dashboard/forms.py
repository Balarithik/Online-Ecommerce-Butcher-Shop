from store.models import Products

from django import forms

class ProductForm(forms.Form):
    class Meta:
        model = Products
        fields = ['name','price','description','image1','image2','image3','image4']