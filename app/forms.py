from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form."""

    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    telefono = forms.CharField(required=True)

    class Meta:
        """Meta class."""

        model = get_user_model()
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "telefono",
            "password1",
            "password2",
        )
