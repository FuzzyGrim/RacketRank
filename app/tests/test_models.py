import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from app.models import Match, Participant, Set, Tournament


class TournamentModelTests(TestCase):
    """Test cases for the Tournament model."""

    def setUp(self):
        """Set up test data."""
        self.User = get_user_model()
        credentials = {
            "username": "test",
            "password": "12345",
            "telefono": "+34666555444",
        }
        self.user1 = self.User.objects.create_user(**credentials)

        credentials2 = {
            "username": "test2",
            "password": "12345",
            "telefono": "+34666555445",
        }
        self.user2 = self.User.objects.create_user(**credentials2)

        self.tournament = Tournament.objects.create(
            name="Test Tournament",
            inscription_end_date=timezone.now().date() + datetime.timedelta(days=5),
            start_date=timezone.now().date() + datetime.timedelta(days=7),
            end_date=timezone.now().date() + datetime.timedelta(days=14),
            image="http://example.com/image.jpg",
            description="Test tournament description",
        )

    def test_tournament_status(self):
        """Test the status property of the Tournament model."""
        self.assertEqual(self.tournament.status, "Inscripciones abiertas")

        # Test status after start date
        self.tournament.start_date = timezone.now().date() - datetime.timedelta(days=1)
        self.tournament.save()
        self.assertEqual(self.tournament.status, "En curso")

        # Test finished status
        self.tournament.current_round = "finalizado"
        self.tournament.save()
        self.assertEqual(self.tournament.status, "Finalizado")

    def test_next_round(self):
        """Test the next_round property of the Tournament model."""
        self.assertEqual(self.tournament.next_round, "octavos")
        self.tournament.current_round = "octavos"
        self.assertEqual(self.tournament.next_round, "cuartos")
        self.tournament.current_round = "final"
        self.assertEqual(self.tournament.next_round, "finalizado")

    def test_distribute_points(self):
        """Test the distribute_points method of the Tournament model."""
        participant1 = Participant.objects.create(
            user=self.user1,
            tournament=self.tournament,
            status="active",
            matches_won=3,
        )
        participant2 = Participant.objects.create(
            user=self.user2,
            tournament=self.tournament,
            status="active",
            matches_won=2,
        )

        self.tournament.distribute_points()

        participant1.refresh_from_db()
        participant2.refresh_from_db()

        self.assertEqual(participant1.score, 2000)  # Winner gets 2000 points
        self.assertEqual(participant2.score, 1500)  # Runner-up gets 1500 points

    def test_participant_creation(self):
        """Test participant creation and properties."""
        participant = Participant.objects.create(
            user=self.user1,
            tournament=self.tournament,
            status="active",
        )
        self.assertEqual(participant.position, "Participante")
        self.assertEqual(participant.score, 0)


class MatchLogicTests(TestCase):
    """Test cases for match logic."""

    def setUp(self):
        """Set up test data."""
        self.User = get_user_model()
        credentials = {
            "username": "test",
            "password": "12345",
            "telefono": "+34666555444",
        }
        self.user1 = self.User.objects.create_user(**credentials)

        credentials2 = {
            "username": "test2",
            "password": "12345",
            "telefono": "+34666555445",
        }
        self.user2 = self.User.objects.create_user(**credentials2)

        self.tournament = Tournament.objects.create(
            name="Test Tournament",
            inscription_end_date=timezone.now().date() + datetime.timedelta(days=5),
            start_date=timezone.now().date() + datetime.timedelta(days=7),
            end_date=timezone.now().date() + datetime.timedelta(days=14),
            image="http://example.com/image.jpg",
            description="Test tournament description",
            current_round="octavos",
        )

        self.participant1 = Participant.objects.create(
            user=self.user1,
            tournament=self.tournament,
            status="active",
        )
        self.participant2 = Participant.objects.create(
            user=self.user2,
            tournament=self.tournament,
            status="active",
        )

        self.match = Match.objects.create(
            tournament=self.tournament,
            participant1=self.participant1,
            participant2=self.participant2,
            date=timezone.now(),
            round="octavos",
        )

    def test_match_winner_calculation(self):
        """Test the winner property of the Match model."""
        # Create sets where participant1 wins
        Set.objects.create(
            match=self.match,
            set_number=1,
            participant1_score=6,
            participant2_score=4,
        )
        Set.objects.create(
            match=self.match,
            set_number=2,
            participant1_score=6,
            participant2_score=3,
        )
        Set.objects.create(
            match=self.match,
            set_number=3,
            participant1_score=6,
            participant2_score=2,
        )

        self.assertEqual(self.match.winner, self.participant1)

    def test_match_settlement(self):
        """Test the settle method of the Match model."""
        # Create sets
        Set.objects.create(
            match=self.match,
            set_number=1,
            participant1_score=6,
            participant2_score=4,
        )
        Set.objects.create(
            match=self.match,
            set_number=2,
            participant1_score=6,
            participant2_score=3,
        )

        self.match.settle()

        self.participant1.refresh_from_db()
        self.participant2.refresh_from_db()

        self.assertEqual(self.participant1.games_won, 12)
        self.assertEqual(self.participant2.games_won, 7)
        self.assertEqual(self.participant1.sets_won, 2)
        self.assertEqual(self.participant2.status, "eliminated")
