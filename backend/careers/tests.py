from django.test import TestCase

from .models import JobApplication


class JobApplicationModelTests(TestCase):

    """Test the JobApplication model functionality."""

    def test_string_representation(self):
        """Verify that the application string representation
        returns the applicant name and job title.
        """
        application = JobApplication.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            mobile_number="+911234567890",
            job_title="Architect",
            description="I would like to apply.",
        )

        self.assertEqual(str(application), "Jane Doe - Architect")
