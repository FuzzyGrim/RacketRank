from django.shortcuts import render


def index(request):
    context = {}
    return render(request, "app/index.html", context)