from django.shortcuts import render


def login(request):
    context = {}
    return render(request, "app/login.html", context)

def register(request):
def password_reset(request):
    context = {}
    return render(request, "app/password-reset.html", context)