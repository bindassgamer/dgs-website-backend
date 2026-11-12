
from django.test import TestCase
from django.urls import reverse

from .models import Person


class PersonModelTests(TestCase):

    """Test the Person model functionality."""

    def test_string_representation(self):
        """Verify that the person string representation returns their name."""
        person = Person.objects.create(
            name="Jane Doe",
            title="Director",
            role="2",
        )

        self.assertEqual(str(person), "Jane Doe")


class PeopleApiTests(TestCase):

    """Test the People API endpoints."""

    def setUp(self):
        """Create sample people records for API tests."""
        self.founder = Person.objects.create(
            name="Jane Doe",
            title="Founder and CEO",
            role="1",
            description="Founder description",
        )
        Person.objects.create(
            name="Alex Smith",
            title="Director",
            role="2",
            description="Director description",
        )

    def test_list_filters_by_role_and_returns_person_ids(self):
        """Verify that the people list filters by role and
        returns person IDs.
        """
        response = self.client.get(
            reverse("people:get-people-list"),
            {"role": "Founder"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "id": self.founder.pk,
                    "name": "Jane Doe",
                    "title": "Founder and CEO",
                }
            ],
        )

    def test_list_requires_a_valid_role(self):
        """Verify that the people list rejects invalid role values."""
        response = self.client.get(
            reverse("people:get-people-list"),
            {"role": "manager"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_detail_includes_description(self):
        """Verify that the person detail API includes the description."""
        response = self.client.get(
            reverse("people:get-people-details"),
            {"person_id": self.founder.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "name": "Jane Doe",
                "title": "Founder and CEO",
                "description": "Founder description",
            },
        )
