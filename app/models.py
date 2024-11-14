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

    def __str__(self):
        """Return name."""
        return self.name
