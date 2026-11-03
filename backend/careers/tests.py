from django.test import TestCase

from .models import JobApplication


class JobApplicationModelTests(TestCase):
    def test_string_representation(self):
        application = JobApplication.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            mobile_number="+911234567890",
            job_title="Architect",
            description="I would like to apply.",
        )

        self.assertEqual(str(application), "Jane Doe - Architect")
