from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import PasswordResetView
from django.core.management.utils import get_random_secret_key
from django.shortcuts import redirect, render
from django_email_verification import send_email

from app import models
from app.forms import CustomUserCreationForm


def home(request):
    """Home view."""
    primavera = models.Tournament.objects.get(name="Primavera")
    verano = models.Tournament.objects.get(name="Verano")
    otono = models.Tournament.objects.get(name="Otoño")
    invierno = models.Tournament.objects.get(name="Invierno")
    context = {
        "primavera": primavera,
        "verano": verano,
        "otono": otono,
        "invierno": invierno,
    }
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


def tournament(request, tournament):
    """Tournament view."""
    tournament = models.Tournament.objects.get(name=tournament.capitalize())
    context = {"tournament": tournament}
    return render(request, "app/tournament.html", context)


def clasificacion(request, tournament):
    """Clasificacion view."""
    tournament = models.Tournament.objects.get(name=tournament.capitalize())
    context = {"tournament": tournament}
    return render(request, "app/clasificacion.html", context)


def partidos(request, tournament):
    """Partidos view."""
    tournament = models.Tournament.objects.get(name=tournament.capitalize())
    context = {"tournament": tournament}
    return render(request, "app/partidos.html", context)
