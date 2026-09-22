from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CustomerSignupForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'password1', 'password2')
        widgets = {
            'username': __import__('django').forms.TextInput(attrs={'class': 'w-full mt-xs px-md py-3 rounded-lg border border-outline-variant'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'w-full mt-xs px-md py-3 rounded-lg border border-outline-variant'
            field.widget.attrs['autocomplete'] = 'new-password' if name.startswith('password') else 'username'
