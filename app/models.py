from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    """Custom user model."""

    telefono = PhoneNumberField(unique=True)
