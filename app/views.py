from django.contrib import messages
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


def password_reset(request):
    """Password reset view."""
    context = {}
    return render(request, "app/password-reset.html", context)
