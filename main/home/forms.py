from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

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

