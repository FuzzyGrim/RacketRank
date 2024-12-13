import datetime
import logging
from random import shuffle

from django.contrib.auth.models import AbstractUser
from django.db import models, transaction
from django.db.models import F, Q, Sum, Window
from django.db.models.functions import Coalesce, DenseRank, Random
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

logger = logging.getLogger(__name__)

round_choices = [
    ("no_comenzado", "No comenzado"),
    ("octavos", "Octavos de Final"),
    ("cuartos", "Cuartos de Final"),
    ("semifinal", "Semifinal"),
    ("final", "Final"),
    ("finalizado", "Finalizado"),
]


class UserStatistics:
    """Class to handle user statistics calculations."""

    def __init__(self, user):
        """Initialize with user."""
        self.user = user
        self._participants = Participant.objects.filter(user=user)

    @property
    def total_points(self):
        """Calculate total points across all tournaments."""
        return self._participants.aggregate(
            total=Coalesce(Sum("score"), 0),
        )["total"]

    def get_tournament_stats(self):
        """Get detailed tournament statistics including set-by-set breakdown."""
        round_order = {
            "octavos": 1,
            "cuartos": 2,
            "semifinal": 3,
            "final": 4,
        }

        tournaments_data = []

        # Get all finished tournaments for the user
        finished_tournaments = self._participants.filter(
            tournament__current_round="finalizado",
        ).select_related("tournament")

        for participant in finished_tournaments:
            # Get all matches where the user participated
            matches = (
                Match.objects.filter(
                    tournament=participant.tournament,
                )
                .filter(
                    Q(participant1=participant) | Q(participant2=participant),
                )
                .select_related(
                    "participant1",
                    "participant2",
                )
                .order_by("date")
            )

            matches_data = []
            total_sets_won = 0
            total_sets_lost = 0

            for match in matches:
                # Determine if the user was participant1 or participant2
                is_participant1 = match.participant1 == participant
                opponent = (
                    match.participant2.user.username
                    if is_participant1
                    else match.participant1.user.username
                )

                # Get all sets for this match
                match_sets = match.set_set.all().order_by("set_number")
                sets_data = []
                match_sets_won = 0
                match_sets_lost = 0

                for set_obj in match_sets:
                    if is_participant1:
                        games_won = set_obj.participant1_score or 0
                        games_lost = set_obj.participant2_score or 0
                    else:
                        games_won = set_obj.participant2_score or 0
                        games_lost = set_obj.participant1_score or 0

                    # Count sets won/lost
                    if games_won > games_lost:
                        match_sets_won += 1
                        total_sets_won += 1
                    elif games_lost > games_won:
                        match_sets_lost += 1
                        total_sets_lost += 1

                    sets_data.append(
                        {
                            "set_number": set_obj.set_number,
                            "games_won": games_won,
                            "games_lost": games_lost,
                            "result": "Won"
                            if games_won > games_lost
                            else "Lost"
                            if games_won < games_lost
                            else "Tie",
                        },
                    )

                matches_data.append(
                    {
                        "round": match.round,
                        "round_order": round_order.get(match.round, 0),  # For sorting
                        "opponent": opponent,
                        "date": match.date,
                        "sets_won": match_sets_won,
                        "sets_lost": match_sets_lost,
                        "sets": sets_data,
                        "result": "Won"
                        if match_sets_won > match_sets_lost
                        else "Lost"
                        if match_sets_won < match_sets_lost
                        else "Tie",
                    },
                )

            # Sort matches by round order
            matches_data.sort(key=lambda x: x["round_order"])

            # Remove round_order as it's no longer needed
            for match in matches_data:
                del match["round_order"]

            tournaments_data.append(
                {
                    "tournament_name": participant.tournament.name,
                    "score": participant.score,
                    "total_games_won": participant.games_won,
                    "total_games_lost": participant.games_lost,
                    "total_sets_won": total_sets_won,
                    "total_sets_lost": total_sets_lost,
                    "matches": matches_data,
                },
            )

        return tournaments_data

    @property
    def overall_ranking(self):
        """Calculate overall ranking based on total points."""
        ranking = (
            User.objects.annotate(
                total_score=Coalesce(
                    Sum("tournaments__participant__score"),
                    0,
                ),
                rank=Window(
                    expression=DenseRank(),
                    order_by=F("total_score").desc(),
                ),
            )
            .filter(
                id=self.user.id,
            )
            .values_list("rank", flat=True)
            .first()
        )

        return ranking or 0


class User(AbstractUser):
    """Custom user model."""

    telefono = PhoneNumberField(unique=True)

    def get_statistics(self):
        """Get user statistics."""
        return UserStatistics(self)


class UserTournamentManager(models.Manager):
    """Manager for user tournament-related queries."""

    def get_played_tournaments(self, user):
        """Return tournaments where the user has participated and which are finished."""
        return self.filter(
            participants=user,
            participant__status__in=["active", "eliminated"],
            current_round="finalizado",
        ).select_related()

    def get_registered_tournaments(self, user):
        """Return tournaments where the user has registered but haven't started."""
        today = timezone.now().date()
        return self.filter(
            participants=user,
            participant__status="applied",
            start_date__gt=today,
        ).select_related()

    def get_active_tournaments(self, user):
        """Return tournaments where the user will participate."""
        return self.filter(
            participants=user,
            participant__status="active",
            current_round="no_comenzado",
        ).select_related()


class Tournament(models.Model):
    """Tournament model."""

    name = models.CharField(max_length=255)
    inscription_end_date = models.DateField()
    start_date = models.DateField()
    end_date = models.DateField()
    image = models.URLField()
    description = models.TextField()

    participants = models.ManyToManyField(
        User,
        through="Participant",
        related_name="tournaments",
    )
    current_round = models.CharField(
        max_length=255,
        choices=round_choices,
        default="no_comenzado",
    )

    objects = UserTournamentManager()

    def __str__(self):
        """Return name."""
        return self.name

    @property
    def status(self):
        """Return status."""
        today = timezone.now().date()
        if self.current_round == "finalizado":
            return "Finalizado"
        if self.current_round == "no_comenzado" and today < self.start_date:
            return "Inscripciones abiertas"
        if today < self.start_date:
            return "Inscripciones cerradas"
        return "En curso"

    @property
    def status_color(self):
        """Return status color."""
        if self.status == "Inscripciones abiertas":
            return "green"
        if self.status == "Inscripciones cerradas":
            return "orange"
        if self.status == "En curso":
            return "blue"
        return "red"

    @property
    def next_round(self):
        """Return next round."""
        next_round = {
            "no_comenzado": "octavos",
            "octavos": "cuartos",
            "cuartos": "semifinal",
            "semifinal": "final",
            "final": "finalizado",
        }
        return next_round.get(self.current_round, None)

    @property
    def readable_next_round(self):
        """Return readable round."""
        return {
            "no_comenzado": "No comenzado",
            "octavos": "Octavos de Final",
            "cuartos": "Cuartos de Final",
            "semifinal": "Semifinal",
            "final": "Final",
            "finalizado": "Finalizado",
        }[self.next_round]

    @property
    def round_finished(self):
        """Return if the current round is finished."""
        # check if all games have winners
        matches = self.match_set.filter(round=self.current_round)
        return all(match.winner for match in matches)

    def select_participants(self, max_participants=16):
        """Select participants for the tournament.

        Only selects from users who have applied to the tournament.
        """
        # Get all applied participants
        applied_participants = self.participant_set.filter(
            status="applied",
        ).select_related("user")

        # Annotate participants with their global statistics
        ranked_participants = applied_participants.annotate(
            total_score=Coalesce(
                Sum(
                    "user__tournaments__participant__score",
                    filter=Q(user__tournaments__current_round="finalizado"),
                ),
                0,
            ),
            total_sets_won=Coalesce(
                Sum(
                    "user__tournaments__participant__sets_won",
                    filter=Q(user__tournaments__current_round="finalizado"),
                ),
                0,
            ),
            total_games_won=Coalesce(
                Sum(
                    "user__tournaments__participant__games_won",
                    filter=Q(user__tournaments__current_round="finalizado"),
                ),
                0,
            ),
            total_games_lost=Coalesce(
                Sum(
                    "user__tournaments__participant__games_lost",
                    filter=Q(user__tournaments__current_round="finalizado"),
                ),
                0,
            ),
        ).order_by(
            F("total_score").desc(),
            F("total_sets_won").desc(),
            F("total_games_won").desc(),
            F("total_games_lost"),
            Random(),
        )[:max_participants]

        # Update status of selected and non-selected participants
        with transaction.atomic():
            # Set selected participants to active
            selected_ids = ranked_participants.values_list("id", flat=True)
            self.participant_set.filter(id__in=selected_ids).update(
                status="active",
            )

    def settle_round(self):
        """Settle the current round."""
        matches = self.match_set.filter(round=self.current_round)
        for match in matches:
            match.settle()

        # cant do it in match settle because there
        # may be players that advance without playing
        participants = self.participant_set.filter(status="active")
        for participant in participants:
            participant.matches_won += 1
            participant.save()

        self.current_round = self.next_round
        self.save()

        self.distribute_points()

        if self.current_round != "finalizado":
            self.generate_matches()

    def distribute_points(self):
        """Return points for given position."""
        points_table = {
            1: 2000,
            2: 1500,
            3: 1000,
            4: 500,
        }

        participants = self.participant_set.exclude(
            status="applied",
        ).order_by(
            F("matches_won").desc(),
            F("sets_won").desc(),
            F("games_won").desc(),
            "games_lost",
            Random(),
        )

        for position, participant in enumerate(participants, 1):
            if position in points_table:
                participant.score = points_table[position]
            else:
                participant.score = 475 - ((position - 5) * 25)
            participant.save()

    def generate_matches(self):
        """Generate matches for the current round and go to the next round."""
        participants = list(
            self.participant_set.exclude(
                status__in=["eliminated", "applied"],
            ),
        )
        shuffle(participants)

        # Crear partidos emparejando de dos en dos
        match_date = timezone.now() + datetime.timedelta(days=2)
        for i in range(0, len(participants) - 1, 2):
            match = Match.objects.create(
                tournament=self,
                participant1=participants[i],
                participant2=participants[i + 1],
                date=match_date,
                round=self.current_round,
            )
            logger.info("Partido creado: %s", match)
            match_date += datetime.timedelta(days=1)


class Participant(models.Model):
    """Participant model."""

    class Status(models.TextChoices):
        """Status choices."""

        APPLIED = "applied", "Applied"
        ACTIVE = "active", "Active"
        ELIMINATED = "eliminated", "Eliminated"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(default=0)
    matches_won = models.PositiveIntegerField(default=0)
    sets_won = models.PositiveIntegerField(default=0)
    games_won = models.PositiveIntegerField(default=0)
    games_lost = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.APPLIED,
    )

    def __str__(self):
        """Return user."""
        return self.user.username

    @property
    def position(self):
        """Return position."""
        position = {
            "1": "Octavofinalista",
            "2": "Cuartofinalista",
            "3": "Semifinalista",
            "4": "Finalista",
            "5": "Campeón",
        }
        return position.get(str(self.matches_won), "Participante")


class Match(models.Model):
    """Match model."""

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    participant1 = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="participant1",
    )
    participant2 = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="participant2",
    )
    date = models.DateTimeField()
    round = models.CharField(max_length=255, choices=round_choices)

    class Meta:
        """Meta class."""

        ordering = ["tournament", "date"]

    def __str__(self):
        """Return match."""
        return f"{self.participant1} vs {self.participant2}"

    def settle(self):
        """Settle the match."""
        for set_played in self.set_set.all():
            if (
                set_played.participant1_score is None
                or set_played.participant2_score is None
            ):
                continue
            self.participant1.games_won += set_played.participant1_score
            self.participant2.games_won += set_played.participant2_score

            self.participant1.games_lost += set_played.participant2_score
            self.participant2.games_lost += set_played.participant1_score

            if set_played.participant1_score > set_played.participant2_score:
                self.participant1.sets_won += 1
            else:
                self.participant2.sets_won += 1

        if self.winner == self.participant1:
            self.participant2.status = Participant.Status.ELIMINATED
        else:
            self.participant1.status = Participant.Status.ELIMINATED

        self.participant1.save()
        self.participant2.save()

    @property
    def participant1_set_wins(self):
        """Return number of sets won by participant1."""
        return self.set_set.filter(
            participant1_score__gt=F("participant2_score"),
        ).count()

    @property
    def participant2_set_wins(self):
        """Return number of sets won by participant2."""
        return self.set_set.filter(
            participant2_score__gt=F("participant1_score"),
        ).count()

    @property
    def winner(self):
        """Return match winner."""
        participant1_sets_win = self.participant1_set_wins
        participant2_sets_win = self.participant2_set_wins

        if participant1_sets_win > participant2_sets_win:
            return self.participant1
        if participant1_sets_win < participant2_sets_win:
            return self.participant2
        return None


class Set(models.Model):
    """Set model."""

    set_number = models.PositiveIntegerField()
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    participant1_score = models.PositiveIntegerField(null=True, blank=True)
    participant2_score = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        """Meta class."""

        ordering = ["set_number"]

    def __str__(self):
        """Return match."""
        return f"{self.participant1_score} - {self.participant2_score}"

    @property
    def winner(self):
        """Return winner."""
        if self.participant1_score > self.participant2_score:
            return self.match.participant1
        if self.participant1_score < self.participant2_score:
            return self.match.participant2
        return None
