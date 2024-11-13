from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import PasswordResetView
from django.core.management.utils import get_random_secret_key
from django.shortcuts import redirect, render

from .forms import CustomUserCreationForm


def home(request):
    """Home view."""
    context = {}
    return render(request, "app/home.html", context)


def register(request):
    """Register view."""
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.",
            )
            return redirect("login")
    else:
        form = CustomUserCreationForm()

    return render(request, "app/register.html", {"form": form})


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view."""

    template_name = "app/password-reset.html"
    subject_template_name = "app/password_reset_subject.txt"
    email_template_name = "app/password_reset_email.html"
    extra_email_context = {"new_password": get_random_secret_key()}

    def form_valid(self, form):
        """Override form_valid to set random password instead of sending reset link."""
        email = form.cleaned_data["email"]
        user = get_user_model().objects.get(email=email)

        if user:
            # Generate and set new password
            new_password = self.extra_email_context["new_password"]
            user.set_password(new_password)
            user.save()

        return super().form_valid(form)
