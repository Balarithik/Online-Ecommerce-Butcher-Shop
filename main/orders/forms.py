# forms.py
from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    address = forms.CharField(max_length=500, required=True)
    quantity = forms.FloatField(required=True)

    class Meta:
        model = Order
        fields = ['name', 'mobile', 'instructions']