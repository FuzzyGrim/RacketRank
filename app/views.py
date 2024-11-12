from django.shortcuts import render


def login(request):
    context = {}
    return render(request, "app/login.html", context)

def register(request):
    context = {}
    return render(request, "app/register.html", context)
