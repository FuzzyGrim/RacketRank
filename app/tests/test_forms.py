from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from app.forms import CustomUserCreationForm, UserProfileForm, create_set_formset
from app.models import Match, Participant, Set, Tournament


class FormsTests(TestCase):
    """Test cases for custom forms."""

    def setUp(self):
        """Set up test data."""
        self.User = get_user_model()
        self.user_data = {
            "username": "testuser",
            "password1": "testpass123",
            "password2": "testpass123",
            "telefono": "+34666555444",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        }

    def test_custom_user_creation_form(self):
        """Test custom user creation form."""
        form = CustomUserCreationForm(data=self.user_data)
        self.assertTrue(form.is_valid())

    def test_user_profile_form(self):
        """Test user profile form."""
        credentials = {
            "username": "test",
            "password": "12345",
            "telefono": "+34666555444",
        }
        user = self.User.objects.create_user(**credentials)
        form_data = {
            "username": "updated",
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
            "telefono": "+34666555444",
        }
        form = UserProfileForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid())


class SetFormTests(TestCase):
    """Test cases for the Set form and formset."""

    def setUp(self):
        """Set up test data."""
        self.User = get_user_model()

        credentials = {
            "username": "test",
            "first_name": "John",
            "last_name": "Doe",
            "password": "12345",
            "telefono": "+34666555444",
        }
        self.user1 = self.User.objects.create_user(**credentials)

        credentials2 = {
            "username": "test2",
            "first_name": "Jane",
            "last_name": "Smith",
            "password": "12345",
            "telefono": "+34666555445",
        }
        self.user2 = self.User.objects.create_user(**credentials2)

        # Create tournament
        self.tournament = Tournament.objects.create(
            name="Test Tournament",
            inscription_end_date=timezone.now().date(),
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=7),
            image="http://example.com/image.jpg",
            description="Test tournament description",
        )

        # Create participants
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

        # Create match
        self.match = Match.objects.create(
            tournament=self.tournament,
            participant1=self.participant1,
            participant2=self.participant2,
            date=timezone.now(),
            round="octavos",
        )

    def test_formset_creation_new_match(self):
        """Test formset creation for a new match without existing sets."""
        set_formset = create_set_formset(self.match)
        formset = set_formset(queryset=Set.objects.none())

        self.assertEqual(len(formset.forms), 5)  # Should have 5 empty forms

        # Verify form labels contain player names
        form = formset.forms[0]
        self.assertIn("John Doe", form.fields["participant1_score"].label)
        self.assertIn("Jane Smith", form.fields["participant2_score"].label)

    def test_formset_creation_existing_match(self):
        """Test formset creation for a match with existing sets."""
        # Create some existing sets
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

        SetFormSet = create_set_formset(self.match)
        formset = SetFormSet(queryset=Set.objects.filter(match=self.match))

        self.assertEqual(len(formset.forms), 2)  # Should have 2 forms for existing sets

        # Verify existing data is loaded
        self.assertEqual(formset.forms[0].instance.participant1_score, 6)
        self.assertEqual(formset.forms[0].instance.participant2_score, 4)

    def test_formset_validation(self):
        """Test form validation rules."""
        SetFormSet = create_set_formset(self.match)

        valid_data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-match": self.match.id,
            "form-0-set_number": 1,
            "form-0-participant1_score": 6,
            "form-0-participant2_score": 4,
        }

        formset = SetFormSet(data=valid_data)
        self.assertTrue(formset.is_valid())

    def test_formset_validation_negative_scores(self):
        """Test validation of negative scores."""
        SetFormSet = create_set_formset(self.match)

        invalid_data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-match": self.match.id,
            "form-0-set_number": 1,
            "form-0-participant1_score": -1,  # Invalid negative score
            "form-0-participant2_score": 4,
        }

        formset = SetFormSet(data=invalid_data)
        self.assertFalse(formset.is_valid())

    def test_formset_save(self):
        """Test saving formset data."""
        SetFormSet = create_set_formset(self.match)

        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-match": self.match.id,
            "form-0-set_number": 1,
            "form-0-participant1_score": 6,
            "form-0-participant2_score": 4,
            "form-1-match": self.match.id,
            "form-1-set_number": 2,
            "form-1-participant1_score": 6,
            "form-1-participant2_score": 3,
        }

        formset = SetFormSet(data=data)
        self.assertTrue(formset.is_valid())
        instances = formset.save()

        self.assertEqual(len(instances), 2)
        self.assertEqual(Set.objects.count(), 2)

        # Verify saved data
        saved_set = Set.objects.first()
        self.assertEqual(saved_set.participant1_score, 6)
        self.assertEqual(saved_set.participant2_score, 4)

    def test_widget_attributes(self):
        """Test that form widgets have correct attributes."""
        set_formset = create_set_formset(self.match)
        formset = set_formset(queryset=Set.objects.none())
        form = formset.forms[0]

        # Test hidden match field
        self.assertIsInstance(form.fields["match"].widget, forms.HiddenInput)

        # Test readonly and hidden set_number field
        self.assertTrue(form.fields["set_number"].widget.attrs.get("readonly"))
        self.assertTrue(form.fields["set_number"].widget.attrs.get("hidden"))

        # Test score fields are not required
        self.assertFalse(form.fields["participant1_score"].widget.attrs.get("required"))
        self.assertFalse(form.fields["participant2_score"].widget.attrs.get("required"))
