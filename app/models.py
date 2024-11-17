import datetime
import logging
from random import shuffle

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F
from django.db.models.functions import Random
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


class User(AbstractUser):
    """Custom user model."""

    telefono = PhoneNumberField(unique=True)


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
