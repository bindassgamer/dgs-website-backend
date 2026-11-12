from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .models import Project, ProjectAmenityPlace, ProjectPhoto


class ProjectModelTests(TestCase):

    """Test the Project, ProjectPhoto, and ProjectAmenityPlace models."""

    def setUp(self):
        """Create a sample project for use in model tests."""
        self.project = Project.objects.create(
            name="DGS Residency",
            description="Residential project",
            price_budget="12500000.00",
            configuration=Project.CONFIGURATION_2BHK,
        )

    def test_project_string_representation(self):
        """Test that the project string representation returns its name."""
        self.assertEqual(str(self.project), "DGS Residency")

    def test_brochure_accepts_pdf_extension(self):
        """Test that the project brochure accepts PDF files."""
        self.project.brochure = SimpleUploadedFile(
            "brochure.pdf",
            b"%PDF-1.4 test document",
            content_type="application/pdf",
        )

        self.project.full_clean()

    def test_brochure_rejects_non_pdf_extension(self):
        """Test that the project brochure rejects files
        with non-PDF extensions.
        """
        self.project.brochure = SimpleUploadedFile(
            "brochure.txt",
            b"not a PDF",
            content_type="text/plain",
        )

        with self.assertRaises(ValidationError):
            self.project.full_clean()

    def test_photo_and_place_are_related_to_project(self):
        """Test that project photos and amenity
        places are related to the project.
        """
        photo = ProjectPhoto.objects.create(
            project=self.project,
            title="Exterior",
            file=SimpleUploadedFile("exterior.jpg", b"image"),
        )
        place = ProjectAmenityPlace.objects.create(
            project=self.project,
            name="City park",
            type=ProjectAmenityPlace.TYPE_PARK,
        )

        self.assertEqual(self.project.photographs.get(), photo)
        self.assertEqual(self.project.amenities_and_places.get(), place)
