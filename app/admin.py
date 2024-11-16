from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from app.models import Match, Participant, Tournament, User


class ParticipantInline(admin.TabularInline):
    """
    Inline admin interface for Participant model.

    Allows adding and editing participants directly from the Tournament admin page.
    """

    model = Participant
    extra = 1


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    """
    Admin interface for Tournament model.

    Provides a customized interface for managing tournaments, including:
    - List display with key tournament information
    - Filtering by round and start date
    - Search functionality
    - Horizontal filter for managing registered users
    - Inline participant management
    """

    list_display = (
        "name",
        "inscription_end_date",
        "start_date",
        "end_date",
        "current_round",
    )
    list_filter = ("current_round", "start_date")
    search_fields = ("name",)
    filter_horizontal = ("registered",)
    inlines = [ParticipantInline]

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "description", "image"),
            },
        ),
        (
            _("Dates"),
            {
                "fields": ("inscription_end_date", "start_date", "end_date"),
            },
        ),
        (
            _("Tournament Status"),
            {
                "fields": ("current_round", "registered"),
            },
        ),
    )


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Admin interface for User model.

    Provides a customized interface for managing users, including:
    - List display with essential user information
    - Search functionality for username, email, and phone number
    """

    list_display = ("username", "email", "telefono", "is_staff")
    search_fields = ("username", "email", "telefono")


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    """
    Admin interface for Participant model.

    Provides a customized interface for managing tournament participants, including:
    - List display showing user, tournament, and score
    - Filtering by tournament
    - Search functionality for user and tournament names
    """

    list_display = ("user", "tournament", "score")
    list_filter = ("tournament",)
    search_fields = ("user__username", "tournament__name")


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    """
    Admin interface for Match model.

    Provides a customized interface for managing tournament matches, including:
    - List display showing match details
    - Filtering by tournament and round
    - Search functionality for tournament and participant names
    """

    list_display = ("tournament", "participant1", "participant2", "date", "round")
    list_filter = ("tournament", "round")
    search_fields = (
        "tournament__name",
        "participant1__user__username",
        "participant2__user__username",
    )
