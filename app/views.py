from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

from .forms import CustomUserCreationForm


def home(request):
    """Home view."""
    context = {}
    return render(request, "app/home.html", context)


def login_view(request):
    """Login view."""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f"¡Bienvenido de vuelta, {username}!")
                return redirect("home")
    else:
        form = AuthenticationForm()

    return render(request, "app/login.html", {"form": form})


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
