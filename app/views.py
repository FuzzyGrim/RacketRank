from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import PasswordResetView
from django.core.management.utils import get_random_secret_key
from django.shortcuts import redirect, render
from django_email_verification import send_email

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
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            send_email(user)
            messages.success(
                request,
                "Hemos enviado un correo electrónico para verificar tu cuenta.",
            )
            return redirect("login")
    else:
        form = CustomUserCreationForm()

    return render(request, "app/register.html", {"form": form})


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view."""

    template_name = "app/reset/password-reset.html"
    subject_template_name = "app/reset/password_reset_subject.txt"
    email_template_name = "app/reset/password_reset_email.html"
    extra_email_context = {"new_password": get_random_secret_key()}

    def form_valid(self, form):
        """Override form_valid to set random password instead of sending reset link."""
        email = form.cleaned_data["email"]
        user = get_user_model().objects.filter(email=email).first()

        if user:
            # Generate and set new password
            new_password = self.extra_email_context["new_password"]
            user.set_password(new_password)
            user.save()

        return super().form_valid(form)
