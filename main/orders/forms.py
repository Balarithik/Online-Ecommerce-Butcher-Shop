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
    )

    def clean_mobile(self):
        mobile = ''.join(filter(str.isdigit, self.cleaned_data.get('mobile') or ''))
        if len(mobile) != 10:
            raise forms.ValidationError('Enter a valid 10-digit mobile number.')
        return mobile

    class Meta:
        model = Order
        fields = ['name', 'mobile', 'instructions']
