from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from phonenumber_field.formfields import PhoneNumberField


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


class UserProfileForm(UserChangeForm):
    """Form for updating user profile."""

    password = None  # Remove password field from UserChangeForm
    new_password = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
    )
    telefono = PhoneNumberField()

    class Meta:
        """Meta class."""

        model = get_user_model()
        fields = ["username", "telefono"]

    def clean(self):
        """Validate the form data."""
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and not confirm_password:
            msg = "Please confirm your password"
            raise forms.ValidationError(msg)

        if new_password and confirm_password and new_password != confirm_password:
            msg = "Passwords do not match"
            raise forms.ValidationError(msg)

        return cleaned_data

    def save(self, commit=True):
        """Save the form data."""
        user = super().save(commit=False)

        if self.cleaned_data.get("new_password"):
            user.set_password(self.cleaned_data["new_password"])

        if commit:
            user.save()

        return user
