# https://docs.djangoproject.com/en/stable/topics/http/urls/#registering-custom-path-converters


class TournamentChecker:
    """Check if the media type is valid."""

    tournaments = ["Primavera", "Verano", "Otoño", "Invierno"]
    regex = f"({'|'.join(tournaments)})"

    def to_python(self, value):
        """Return the media type if it is valid."""
        return value

    def to_url(self, value):
        """Return the media type if it is valid."""
        return value
