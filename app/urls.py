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
    path(
        "password-reset/",
        views.CustomPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="app/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path("logout", auth_views.LogoutView.as_view(), name="logout"),
]
