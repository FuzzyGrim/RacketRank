from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib import messages

def login(request):
    context = {}
    return render(request, "app/login.html", context)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'app/register.html', {'form': form})

def password_reset(request):
    context = {}
    return render(request, "app/password-reset.html", context)