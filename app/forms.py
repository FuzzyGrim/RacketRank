from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.forms import modelformset_factory
from phonenumber_field.formfields import PhoneNumberField

from app.models import Set


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


def create_set_formset(match):
    """Create a formset for match sets."""

    class SetForm(forms.ModelForm):
        """Form for individual sets in a match."""

        class Meta:
            model = Set
            fields = ["match", "set_number", "participant1_score", "participant2_score"]
            labels = {
                "participant1_score": (
                    f"Puntuación de {match.participant1.user.first_name} "
                    f"{match.participant1.user.last_name}"
                ),
                "participant2_score": (
                    f"Puntuación de {match.participant2.user.first_name} "
                    f"{match.participant2.user.last_name}"
                ),
            }
            widgets = {
                "match": forms.HiddenInput(),
                "set_number": forms.TextInput(attrs={"readonly": True, "hidden": True}),
                "participant1_score": forms.NumberInput(attrs={"required": False}),
                "participant2_score": forms.NumberInput(attrs={"required": False}),
            }

    match_sets = Set.objects.filter(match=match)
    extra = 0 if match_sets.exists() else 5

    return modelformset_factory(
        Set,
        form=SetForm,
        extra=extra,
    )
