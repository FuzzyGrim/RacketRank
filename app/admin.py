from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from app.models import Match, Participant, Set, Tournament, User


class ParticipantInline(admin.TabularInline):
    """
    Inline admin interface for Participant model.

    Allows adding and editing participants directly from the Tournament admin page.
    Shows participant status and statistics.
    """

    model = Participant
    extra = 1
    readonly_fields = ("matches_won", "sets_won", "games_won", "games_lost")
    fields = (
        "user",
        "status",
        "score",
        "matches_won",
        "sets_won",
        "games_won",
        "games_lost",
    )


class SetInline(admin.TabularInline):
    """
    Inline admin interface for Set model.

    Allows adding and editing sets directly from the Match admin page.
    Shows set number and scores for both participants.
    """

    model = Set
    extra = 1
    ordering = ("set_number",)


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    """
    Admin interface for Tournament model.

    Provides a customized interface for managing tournaments, including:
    - List display with key tournament information
    - Filtering by round and dates
    - Search functionality
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
                "fields": ("current_round",),
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
    - List display showing user, tournament, status and statistics
    - Filtering by tournament and status
    - Search functionality for user and tournament names
    """

    list_display = ("user", "tournament", "status", "score", "matches_won", "sets_won")
    list_filter = ("tournament", "status")
    search_fields = ("user__username", "tournament__name")
    readonly_fields = ("matches_won", "sets_won", "games_won", "games_lost")


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    """
    Admin interface for Match model.

    Provides a customized interface for managing tournament matches, including:
    - List display showing match details
    - Filtering by tournament and round
    - Search functionality for tournament and participant names
    - Inline management of match sets
    """

    list_display = ("tournament", "participant1", "participant2", "date", "round")
    list_filter = ("tournament", "round")
    search_fields = (
        "tournament__name",
        "participant1__user__username",
        "participant2__user__username",
    )
    inlines = [SetInline]


@admin.register(Set)
class SetAdmin(admin.ModelAdmin):
    """
    Admin interface for Set model.

    Provides a customized interface for managing match sets, including:
    - List display showing set details and scores
    - Filtering by match
    - Ordering by set number
    """

    list_display = ("match", "set_number", "participant1_score", "participant2_score")
    list_filter = ("match__tournament", "match")
    search_fields = (
        "match__participant1__user__username",
        "match__participant2__user__username",
    )
    ordering = ("match", "set_number")
