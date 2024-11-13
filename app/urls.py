from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path(
        "login",
        auth_views.LoginView.as_view(template_name="app/login.html"),
        name="login",
    ),
    path("register", views.register, name="register"),
    path("recovery", views.password_reset, name="recovery"),
    path("logout", auth_views.LogoutView.as_view(), name="logout"),
]
