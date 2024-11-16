from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView
from django.core.management.utils import get_random_secret_key
from django.forms import modelformset_factory
from django.shortcuts import redirect, render
from django_email_verification import send_email

from app import models
from app.forms import CustomUserCreationForm


@login_required
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


@login_required
def tournament(request, tournament):
    """Tournament view."""
    tournament = models.Tournament.objects.get(name=tournament.capitalize())

    if "inscribir" in request.POST:
        tournament.registered.add(request.user)
    elif "desinscribir" in request.POST:
        tournament.registered.remove(request.user)

    user_registered = tournament.registered.filter(id=request.user.id).exists()

    context = {"tournament": tournament, "user_registered": user_registered}
    return render(request, "app/tournament.html", context)


@login_required
def standings(request, tournament):
    """Clasificacion view."""
    tournament = models.Tournament.objects.get(name=tournament.capitalize())
    context = {"tournament": tournament}
    return render(request, "app/standings.html", context)


@login_required
def matches(request, tournament):
    """Match view."""
    tournament_obj = models.Tournament.objects.get(name=tournament.capitalize())

    # Get all rounds with matches
    rounds_with_matches = (
        models.Match.objects.filter(tournament=tournament_obj)
        .values_list("round", flat=True)
        .distinct()
        .order_by("round")
    )

    # Create rounds data structure
    rounds_data = []
    for round_name in rounds_with_matches:
        matches = (
            models.Match.objects.filter(
                tournament=tournament_obj,
                round=round_name,
            )
            .select_related("participant1__user", "participant2__user")
            .prefetch_related("set_set")
        )

        rounds_data.append(
            {
                "name": round_name.capitalize(),
                "matches": matches,
            },
        )

    context = {
        "tournament": tournament_obj,
        "rounds": rounds_data,
        "can_generate_matches": (
            request.user.is_staff
            and tournament_obj.participants.count() > 1
            and tournament_obj.next_round
            and tournament_obj.next_round not in rounds_with_matches
            and tournament_obj.round_finished
        ),
    }
    return render(request, "app/matches.html", context)


@login_required
@staff_member_required
def generate_matches(request, tournament):
    """Generate matches for the next round."""
    if request.method == "POST":
        tournament = models.Tournament.objects.get(name=tournament.capitalize())
        tournament.generate_matches()
        messages.success(request, f"Matches generated for {tournament.current_round}")
    return redirect("matches", tournament=tournament.name.lower())


@login_required
@staff_member_required
def match(request, tournament, match_id):
    """Match view."""
    tournament = models.Tournament.objects.get(name=tournament.capitalize())
    match = models.Match.objects.get(id=match_id)

    match_sets = models.Set.objects.filter(match=match)
    extra = 0 if match_sets.exists() else 5

    set_formset = modelformset_factory(
        models.Set,
        extra=extra,
        fields=("__all__"),
        labels={
            "participant1_score": f"Puntuación de {match.participant1.user.first_name} {match.participant1.user.last_name}",  # noqa: E501
            "participant2_score": f"Puntuación de {match.participant2.user.first_name} {match.participant1.user.last_name}",  # noqa: E501
        },
        widgets={
            "match": forms.HiddenInput(),
            "set_number": forms.TextInput(attrs={"readonly": True, "hidden": True}),
            "participant1_score": forms.NumberInput(attrs={"required": False}),
            "participant2_score": forms.NumberInput(attrs={"required": False}),
        },
    )

    if request.method == "POST":
        formset = set_formset(
            request.POST,
            queryset=match_sets,
        )
        if formset.is_valid():
            formset.save()
            return redirect("matches", tournament=tournament.name.lower())
    else:
        formset = set_formset(
            queryset=match_sets,
            initial=[{"match": match, "set_number": i + 1} for i in range(5)],
        )

    context = {"match": match, "formset": formset, "tournament": tournament}
    return render(request, "app/match.html", context)
