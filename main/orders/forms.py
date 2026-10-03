# forms.py
from django import forms
from decimal import Decimal
from .models import Order

class OrderForm(forms.ModelForm):
    address = forms.CharField(max_length=500, required=True)
    quantity = forms.DecimalField(
        required=True,
        min_value=Decimal('0.250'),
        max_value=Decimal('100.000'),
        decimal_places=3,
        initial=Decimal('1.000')
    )
    delivery_slot = forms.CharField(max_length=100, required=False, initial='Express Delivery (45-60 Mins)')
    cut_preference = forms.CharField(max_length=100, required=False, initial='Curry Cut (Medium)')
    payment_method = forms.CharField(max_length=50, required=False, initial='Cash on Delivery')
    latitude = forms.DecimalField(
        required=False,
        min_value=Decimal('-90'),
        max_value=Decimal('90'),
        max_digits=9,
        decimal_places=6,
    )
    longitude = forms.DecimalField(
        required=False,
        min_value=Decimal('-180'),
        max_value=Decimal('180'),
        max_digits=9,
        decimal_places=6,
    )

    def clean_mobile(self):
        raw_mobile = self.cleaned_data.get('mobile') or ''
        mobile = ''.join(filter(str.isdigit, raw_mobile))
        if len(mobile) == 12 and mobile.startswith('91'):
            mobile = mobile[2:]
        if len(mobile) != 10:
            raise forms.ValidationError('Enter a valid 10-digit mobile number.')
        return mobile

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')
        if (latitude is None) != (longitude is None):
            raise forms.ValidationError('Share both location coordinates, or leave both blank.')
        return cleaned_data

    class Meta:
        model = Order
        fields = [
            'name',
            'mobile',
            'instructions',
            'delivery_slot',
            'cut_preference',
            'payment_method',
            'latitude',
            'longitude',
        ]
