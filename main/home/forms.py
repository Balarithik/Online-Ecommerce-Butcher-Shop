from django import forms

from .models import CustomerFeedback


class CustomerFeedbackForm(forms.ModelForm):
    class Meta:
        model = CustomerFeedback
        fields = ("category", "rating", "message", "contact_email")
        widgets = {
            "category": forms.Select(attrs={"class": "w-full rounded-lg border border-amber-200 px-3 py-2 text-sm"}),
            "rating": forms.Select(attrs={"class": "w-full rounded-lg border border-amber-200 px-3 py-2 text-sm"}),
            "message": forms.Textarea(attrs={
                "rows": 3,
                "maxlength": 1500,
                "placeholder": "Tell us what worked well or what we should improve…",
                "class": "w-full rounded-lg border border-amber-200 px-3 py-2 text-sm",
            }),
            "contact_email": forms.EmailInput(attrs={
                "placeholder": "Email (optional)",
                "class": "w-full rounded-lg border border-amber-200 px-3 py-2 text-sm",
            }),
        }
