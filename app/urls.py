from django.contrib.auth import views as auth_views
from django.urls import path, register_converter

from app import converters, views

register_converter(converters.TournamentChecker, "tournament")

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
            template_name="app/reset/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path("logout", auth_views.LogoutView.as_view(), name="logout"),
    path("torneo/<tournament:tournament>", views.tournament, name="tournament"),
    path(
        "torneo/<tournament:tournament>/clasificación",
        views.standings,
        name="standings",
    ),
    path("torneo/<tournament:tournament>/partidos", views.matches, name="matches"),
    path(
        "torneo/<tournament:tournament>/settle_round/",
        views.settle_round,
        name="settle_round",
    ),
    path(
        "torneo/<tournament:tournament>/partido/<int:match_id>",
        views.match,
        name="match",
    ),
]
