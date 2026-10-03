from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import CustomerAddress, CustomerProfile


INPUT_CLASS = (
    "mt-1 block w-full rounded-xl border border-outline-variant bg-white "
    "px-3 py-2.5 text-sm text-on-surface focus:border-primary "
    "focus:ring-2 focus:ring-primary/20"
)


class CustomerSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=False, label="Full Name", widget=forms.TextInput(attrs={
        'placeholder': 'e.g. Rahul Sharma',
        'class': 'w-full mt-1.5 px-4 py-3 rounded-xl border border-outline-variant bg-surface-bright font-body-md focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all'
    }))
    email = forms.EmailField(required=False, label="Email Address (Optional)", widget=forms.EmailInput(attrs={
        'placeholder': 'e.g. rahul@example.com',
        'class': 'w-full mt-1.5 px-4 py-3 rounded-xl border border-outline-variant bg-surface-bright font-body-md focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all'
    }))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            self.fields['username'].label = "Mobile Number or Username"
            self.fields['username'].widget.attrs.update({
                'placeholder': 'e.g. 9876543210 or username',
                'class': 'w-full mt-1.5 px-4 py-3 rounded-xl border border-outline-variant bg-surface-bright font-body-md focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all'
            })
        for name in ['password1', 'password2']:
            if name in self.fields:
                self.fields[name].widget.attrs.update({
                    'placeholder': '••••••••',
                    'class': 'w-full mt-1.5 px-4 py-3 rounded-xl border border-outline-variant bg-surface-bright font-body-md focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all',
                    'autocomplete': 'new-password'
                })


class CustomerProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": INPUT_CLASS}))
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": INPUT_CLASS}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"class": INPUT_CLASS}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": INPUT_CLASS}))

    class Meta:
        model = CustomerProfile
        fields = ("mobile",)
        widgets = {
            "mobile": forms.TelInput(attrs={
                "class": INPUT_CLASS,
                "maxlength": "10",
                "placeholder": "10-digit mobile number",
            }),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["first_name"].initial = user.first_name
        self.fields["last_name"].initial = user.last_name
        self.fields["email"].initial = user.email
        self.fields["username"].initial = user.username

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username=username).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("That username is already in use.")
        return username

    def clean_mobile(self):
        mobile = "".join(filter(str.isdigit, self.cleaned_data.get("mobile", "")))
        if mobile and len(mobile) == 12 and mobile.startswith("91"):
            mobile = mobile[2:]
        if mobile and len(mobile) != 10:
            raise forms.ValidationError("Enter a valid 10-digit mobile number.")
        return mobile

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.username = self.cleaned_data["username"].strip()
        self.user.first_name = self.cleaned_data["first_name"].strip()
        self.user.last_name = self.cleaned_data["last_name"].strip()
        self.user.email = self.cleaned_data["email"].strip()
        if commit:
            self.user.save()
            profile.save()
        return profile


class CustomerAddressForm(forms.ModelForm):
    class Meta:
        model = CustomerAddress
        fields = (
            "label",
            "recipient_name",
            "mobile",
            "address",
        )
        widgets = {
            "label": forms.Select(attrs={"class": INPUT_CLASS}),
            "recipient_name": forms.TextInput(attrs={"class": INPUT_CLASS}),
            "mobile": forms.TelInput(attrs={"class": INPUT_CLASS, "maxlength": "10"}),
            "address": forms.Textarea(attrs={
                "class": INPUT_CLASS,
                "rows": 3,
                "placeholder": "House / flat, street, area, city and PIN code",
            }),
        }

    def clean_mobile(self):
        mobile = "".join(filter(str.isdigit, self.cleaned_data.get("mobile", "")))
        if len(mobile) == 12 and mobile.startswith("91"):
            mobile = mobile[2:]
        if len(mobile) != 10:
            raise forms.ValidationError("Enter a valid 10-digit mobile number.")
        return mobile
