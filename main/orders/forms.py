# forms.py
from django import forms
from decimal import Decimal
from .models import Order

DELIVERY_SLOT_CHOICES = [
    ('Express Delivery (45-60 Mins)', 'Express Delivery (45-60 Mins)'),
    ('Same Day Delivery', 'Same Day Delivery'),
]

CUT_PREFERENCE_CHOICES = [
    ('Curry Cut (Medium)', 'Curry Cut (Medium)'),
    ('Biryani Cut (Large)', 'Biryani Cut (Large)'),
    ('Small Pieces', 'Small Pieces'),
    ('Whole (Cleaned)', 'Whole (Cleaned)'),
    ('Half (Cleaned)', 'Half (Cleaned)'),
]

PAYMENT_METHOD_CHOICES = [
    ('Cash on Delivery', 'Cash on Delivery'),
    ('UPI / QR Code on Delivery', 'UPI / QR Code on Delivery'),
]


class OrderForm(forms.ModelForm):
    address = forms.CharField(max_length=500, required=True)
    quantity = forms.DecimalField(
        required=True,
        min_value=Decimal('0.250'),
        max_value=Decimal('100.000'),
        decimal_places=3,
        initial=Decimal('1.000')
    )
    delivery_slot = forms.ChoiceField(
        choices=DELIVERY_SLOT_CHOICES,
        required=False,
        initial='Express Delivery (45-60 Mins)',
    )
    cut_preference = forms.ChoiceField(
        choices=CUT_PREFERENCE_CHOICES,
        required=False,
        initial='Curry Cut (Medium)',
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        required=False,
        initial='Cash on Delivery',
    )
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

    def clean_address(self):
        address = (self.cleaned_data.get('address') or '').strip()
        if not address or len(address) < 10:
            raise forms.ValidationError('Please enter a complete delivery address including house/flat and street details.')
        
        parts = [p.strip() for p in address.split(',') if p.strip()]
        non_default_parts = [
            p for p in parts 
            if not p.lower().startswith('pin:') 
            and not p.lower().startswith('near') 
            and p.lower() not in ['uchipuli', '(home)', '(work)', '(other)']
        ]
        if not non_default_parts:
            raise forms.ValidationError('Please enter your house/flat number and street name for delivery.')
            
        return address

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
