# forms.py
from django import forms
from .models import Order

class OrderForm(forms.Form):
    class Meta:
        model = Order
        fields = ['name', 'mobile', 'price', 'location','instructions']
    """widgets = {
            'name': forms.TextInput(attrs={'class': 'input-focus-effect w-full h-12 px-md rounded-lg border border-outline-variant bg-surface-bright font-body-md','placeholder':'eg. John Doe','required': True}),
            'mobile': forms.TextInput(attrs={'class': 'input-focus-effect w-full h-12 px-md rounded-lg border border-outline-variant bg-surface-bright font-body-md','placeholder':'eg. 00000000','required': True,'type': 'tel'}),
            'location': forms.Textarea(attrs={'class': 'input-focus-effect w-full p-md rounded-lg border border-outline-variant bg-surface-bright font-body-md resize-none','placeholder':'Apartment, Street, Area, Landmark','rows': 3,'required': True}),
            'instructions': forms.TextInput(attrs={'class': 'input-focus-effect w-full p-md rounded-lg border border-outline-variant bg-surface-bright font-body-md resize-none','placeholder':'eg. ring the bells twice','required': False}),
        }"""