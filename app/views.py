from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView
from django.core.management.utils import get_random_secret_key
from django.db.models import F, Sum
from django.db.models.functions import Random
from django.shortcuts import redirect, render
from django_email_verification import send_email

from app import models
from app.forms import CustomUserCreationForm, UserProfileForm, create_set_formset


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
        tournament.participants.add(request.user)
    elif "desinscribir" in request.POST:
        tournament.participants.remove(request.user)

    user_applied = tournament.participants.filter(id=request.user.id).exists()

    context = {"tournament": tournament, "user_applied": user_applied}
    return render(request, "app/tournament.html", context)


@login_required
def matches(request, tournament):
    """Match view."""
    tournament_obj = models.Tournament.objects.get(name=tournament.capitalize())

    # Fetch all matches for the tournament with necessary relations in one query
    matches = (
        models.Match.objects.filter(tournament=tournament_obj)
        .order_by("-date")
        .select_related(
            "participant1__user",
            "participant2__user",
            "tournament",
        )
        .prefetch_related("set_set")
    )

    # Group matches by round
    rounds_data = {}
    for match in matches:
        round_name = match.round
        if round_name not in rounds_data:
            rounds_data[round_name] = {
                "name": round_name.capitalize(),
                "matches": [],
            }
        rounds_data[round_name]["matches"].append(match)

    round_order = {
        "octavos": 1,
        "cuartos": 2,
        "semifinal": 3,
        "final": 4,
    }

    # Sort rounds based on predefined order
    sorted_rounds = sorted(
        rounds_data.values(),
        key=lambda x: round_order[x["name"].lower()],
        reverse=True,
    )

    context = {
        "tournament": tournament_obj,
        "rounds": sorted_rounds,
        "can_generate_matches": (
            request.user.is_staff
            and tournament_obj.participants.count() > 1
            and tournament_obj.next_round
            and tournament_obj.round_finished
        ),
    }

    return render(request, "app/matches.html", context)


@login_required
@staff_member_required
def settle_round(request, tournament):
    """Generate matches for the next round."""
    if request.method == "POST":
        tournament = models.Tournament.objects.get(name=tournament.capitalize())
        tournament.settle_round()
    return redirect("matches", tournament=tournament.name.lower())


@login_required
@staff_member_required
def match(request, tournament, match_id):
    """Match view."""
    tournament = models.Tournament.objects.get(name=tournament.capitalize())
    match = models.Match.objects.get(id=match_id)
    match_sets = models.Set.objects.filter(match=match)

    set_formset = create_set_formset(match)

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


@login_required
def standings(request, tournament):
    """Player standings view."""
    tournament = models.Tournament.objects.get(name=tournament.capitalize())
    participants = (
        models.Participant.objects.filter(tournament=tournament)
        .exclude(status="applied")
        .order_by(
        "-score",
        )
    )
    context = {"tournament": tournament, "participants": participants}
    return render(request, "app/standings.html", context)


@login_required
def global_ranking(request):
    """Global ranking view."""
    rankings = (
        get_user_model()
        .objects.annotate(
            total_sets_won=Sum("participant__sets_won"),
            total_games_won=Sum("participant__games_won"),
            total_games_lost=Sum("participant__games_lost"),
            # Add random value for consistent tie-breaking within a single request
            random_order=Random(),
        )
        .filter(
            # Only include users who have participated in tournaments
            participant__isnull=False,
        )
        .order_by(
            # Order by our criteria
            F("total_sets_won").desc(nulls_last=True),
            F("total_games_won").desc(nulls_last=True),
            F("total_games_lost").asc(nulls_last=True),
            "random_order",
        )
        .distinct()
    )
    context = {"rankings": rankings}
    return render(request, "app/global-ranking.html", context)


@login_required
def personal_stats(request):
    """Personal statistics view."""
    user_stats = request.user.get_statistics()

    context = {
        "tournament_stats": user_stats.get_tournament_stats(),
        "total_points": user_stats.total_points,
        "overall_ranking": user_stats.overall_ranking,
    }

    return render(request, "app/personal-stats.html", context)


@login_required
def history(request):
    """User tournaments view."""
    played_tournaments = models.Tournament.objects.get_played_tournaments(request.user)
    played_tournaments_data = []
    for tournament in played_tournaments:
        participant = tournament.participant_set.get(user=request.user)
        played_tournaments_data.append(
            {
                "name": tournament.name,
                "start_date": tournament.start_date,
                "end_date": tournament.end_date,
                "score": participant.score,
                "position": participant.position,
            },
        )

    registered_tournaments = models.Tournament.objects.get_registered_tournaments(
        request.user,
    )
    active_tournaments = models.Tournament.objects.get_active_tournaments(request.user)

    context = {
        "played_tournaments": played_tournaments_data,
        "registered_tournaments": registered_tournaments,
        "active_tournaments": active_tournaments,
    }
    return render(request, "app/history.html", context)


@login_required
def profile(request):
    """Profile view for updating user information."""
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, "app/profile.html", {"form": form})
