import datetime
import logging

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

    def generate_matches(self):
        """Generate matches for the current round."""
        participants = list(self.participant_set.all())

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


class Participant(models.Model):
    """Participant model."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)

    def __str__(self):
        """Return user."""
        return self.user.username


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
        return self.participant2


class Set(models.Model):
    """Set model."""

    set_number = models.IntegerField()
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    participant1_score = models.IntegerField()
    participant2_score = models.IntegerField()

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
        return self.match.participant2
