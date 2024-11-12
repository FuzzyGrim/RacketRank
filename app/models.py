from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    """Custom user model."""

    phone_number = PhoneNumberField(unique=True)
