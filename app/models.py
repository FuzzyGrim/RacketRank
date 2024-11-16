import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


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


class Participant(models.Model):
    """Participant model."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)

    def __str__(self):
        """Return user."""
        return self.user.username
