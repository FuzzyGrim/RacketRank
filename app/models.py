import datetime
import logging
from random import random, shuffle

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

logger = logging.getLogger(__name__)

round_choices = [
    ("octavos", "Octavos de Final"),
    ("cuartos", "Cuartos de Final"),
    ("semifinal", "Semifinal"),
    ("final", "Final"),
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

    registered = models.ManyToManyField(User, related_name="registered")
    participants = models.ManyToManyField(User, through="Participant")
    current_round = models.CharField(
        max_length=255,
        choices=round_choices,
        default="octavos",
    )

    def __str__(self):
        """Return name."""
        return self.name

    @property
    def status(self):
        """Return status."""
        today = datetime.datetime.now(tz=settings.TZ).date()
        if today < self.inscription_end_date:
            return "Inscripciones abiertas"
        if today >= self.inscription_end_date and today < self.start_date:
            return "Inscripciones cerradas"
        if today >= self.start_date and today < self.end_date:
            return "En curso"
        return "Finalizado"

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
            "octavos": "cuartos",
            "cuartos": "semifinal",
            "semifinal": "final",
            "final": None,
        }
        return next_round[self.current_round]

    @property
    def readable_next_round(self):
        """Return readable round."""
        return {
            "octavos": "Octavos de Final",
            "cuartos": "Cuartos de Final",
            "semifinal": "Semifinal",
            "final": "Final",
        }[self.next_round]

    @property
    def round_finished(self):
        """Return if the current round is finished."""
        # check if all games have winners
        matches = self.match_set.filter(round=self.current_round)
        return all(match.winner for match in matches)

    def generate_matches(self):
        """Generate matches for the current round."""
        # get shuffled participants that havent lost
        matches = self.match_set.all()
        participants = list(
            self.participant_set.exclude(
                user__in=[match.loser.user for match in matches if match.loser],
            ),
        )
        shuffle(participants)

        # update round
        self.current_round = self.next_round
        self.save()

        if not participants:
            logger.info("No hay participantes")
            return

        # Crear partidos emparejando de dos en dos
        for i in range(0, len(participants) - 1, 2):
            match = Match.objects.create(
                tournament=self,
                participant1=participants[i],
                participant2=participants[i + 1],
                date=timezone.now(),  # Update
                round=self.current_round,
            )
            logger.info("Partido creado: %s", match)

        return

    def get_position_points(self, position):
        """Return points for given position."""
        points_table = {
            1: 2000,
            2: 1500,
            3: 1000,
            4: 1000,
        }
        if position in points_table:
            return points_table[position]

        return 500 - ((position - 5) * 25)

    def get_standings(self):
        """Return ordered list of participants based on their performance."""
        participants = self.participant_set.all()
        standings = []
        for participant in participants:
            stats = participant.get_statistics()
            standings.append(
                {
                    "participant": participant,
                    "matches_won": stats["matches_won"],
                    "sets_won": stats["sets_won"],
                    "points_won": stats["points_won"],
                    "points_lost": stats["points_lost"],
                    "random_factor": random(),  # noqa: S311
                },
            )

        # Sort standings
        standings = sorted(
            standings,
            key=lambda x: (
                x["matches_won"],
                x["sets_won"],
                x["points_won"],
                -x["points_lost"],
                x["random_factor"],
            ),
            reverse=True,
        )

        # Add tournament points based on position
        for i, standing in enumerate(standings, 1):
            standing["tournament_points"] = self.get_position_points(i)
            standing["participant"].score = standing["tournament_points"]
            standing["participant"].save()

        return standings


class Participant(models.Model):
    """Participant model."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)

    def __str__(self):
        """Return user."""
        return self.user.username

    def get_statistics(self):
        """Calculate match statistics for participant."""
        matches = Match.objects.filter(
            tournament=self.tournament,
        ).filter(
            models.Q(participant1=self) | models.Q(participant2=self),
        )

        matches_won = sum(1 for match in matches if match.winner == self)
        sets_won = 0
        points_won = 0
        points_lost = 0

        for match in matches:
            if match.participant1 == self:
                sets_won += match.participant1_wins
                points_won += match.participant1_points
                points_lost += match.participant2_points
            else:
                sets_won += match.participant2_wins
                points_won += match.participant2_points
                points_lost += match.participant1_points

        return {
            "matches_won": matches_won,
            "sets_won": sets_won,
            "points_won": points_won,
            "points_lost": points_lost,
        }


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

    @property
    def participant1_wins(self):
        """Return participant1 wins."""
        return self.set_set.filter(
            participant1_score__gt=F("participant2_score"),
        ).count()

    @property
    def participant2_wins(self):
        """Return participant2 wins."""
        return self.set_set.filter(
            participant2_score__gt=F("participant1_score"),
        ).count()

    @property
    def winner(self):
        """Return winner."""
        if self.participant1_wins > self.participant2_wins:
            return self.participant1
        if self.participant1_wins < self.participant2_wins:
            return self.participant2
        return None

    @property
    def loser(self):
        """Return loser."""
        if self.participant1_wins > self.participant2_wins:
            return self.participant2
        if self.participant1_wins < self.participant2_wins:
            return self.participant1
        return None

    @property
    def participant1_points(self):
        """Return total points for participant1."""
        return (
            self.set_set.aggregate(
                total=models.Sum("participant1_score"),
            )["total"]
            or 0
        )

    @property
    def participant2_points(self):
        """Return total points for participant2."""
        return (
            self.set_set.aggregate(
                total=models.Sum("participant2_score"),
            )["total"]
            or 0
        )


class Set(models.Model):
    """Set model."""

    set_number = models.IntegerField()
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    participant1_score = models.IntegerField(null=True, blank=True)
    participant2_score = models.IntegerField(null=True, blank=True)

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
