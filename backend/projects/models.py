from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models

from .price import parse_price

LOCATION_LEVELS = range(1, 7)


class Project(models.Model):
    name = models.CharField(max_length=255)
    short_description = models.CharField(max_length=500, blank=True)
    long_description = models.TextField(blank=True)
    # Text shown on the website, e.g. "₹ 2.89 Cr Onwards".
    price_budget = models.CharField(max_length=255)
    # Rupees parsed from price_budget on save; used to filter and search.
    starting_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
        editable=False,
    )
    location_name = models.CharField(max_length=255, blank=True)
    location_1 = models.ForeignKey(
        "geo.Location1",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="projects",
    )
    location_2 = models.ForeignKey(
        "geo.Location2",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="projects",
    )
    location_3 = models.ForeignKey(
        "geo.Location3",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="projects",
    )
    location_4 = models.ForeignKey(
        "geo.Location4",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="projects",
    )
    location_5 = models.ForeignKey(
        "geo.Location5",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="projects",
    )
    location_6 = models.ForeignKey(
        "geo.Location6",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="projects",
    )
    address = models.TextField(blank=True)
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
    )
    contact_phone = models.CharField(max_length=32, blank=True)
    virtual_tour_url = models.URLField(blank=True)
    walkthrough_video_url = models.URLField(blank=True)

    brochure = models.FileField(
        upload_to="projects/brochures/",
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )
    PROJECT_STATUS_CHOICES = (
        ("1", "Completed Project"),
        ("2", "OnGoing Project"),
        ("3", "Upcoming Project"),
    )
    project_status = models.CharField(
        max_length=1,
        choices=PROJECT_STATUS_CHOICES
    )
    is_featured = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        errors = {}
        for level in LOCATION_LEVELS[1:]:
            child = getattr(self, f"location_{level}")
            parent = getattr(self, f"location_{level - 1}")
            if (
                child
                and parent
                and getattr(child, f"location_{level - 1}_id") != parent.pk
            ):
                errors[f"location_{level}"] = (
                    f"This is not inside the selected location {level - 1}."
                )
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.starting_price = parse_price(self.price_budget)
        super().save(*args, **kwargs)

    @property
    def bhk_summary(self):
        counts = list(
            self.configurations.order_by("bhk_count").values_list(
                "bhk_count",
                flat=True,
            )
        )
        if not counts:
            return ""
        if len(counts) == 1:
            return f"{counts[0]} BHK"
        return f"{', '.join(map(str, counts[:-1]))} & {counts[-1]} BHK"

    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"


class ProjectConfiguration(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="configurations",
    )
    bhk_count = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
    )
    carpet_area_sq_ft = models.DecimalField(max_digits=10, decimal_places=2)
    bed_count = models.PositiveSmallIntegerField()
    bathroom_count = models.PositiveSmallIntegerField()
    image = models.FileField(
        upload_to="projects/configurations/",
        blank=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name}: {self.bhk_count} BHK"

    class Meta:
        verbose_name = "Project Configuration"
        verbose_name_plural = "Project Configurations"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "bhk_count"],
                name="unique_project_bhk_configuration",
            ),
        ]


class ProjectPhoto(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="photographs",
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="projects/photographs/")
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name}: {self.title}"

    class Meta:
        verbose_name = "Project Photograph"
        verbose_name_plural = "Project Photographs"


class ProjectAmenity(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="amenities",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.FileField(
        upload_to="projects/amenities/",
        blank=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name}: {self.name}"

    class Meta:
        verbose_name = "Project Amenity"
        verbose_name_plural = "Project Amenities"


class ProjectAmenityPlace(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="amenities_and_places",
    )
    name = models.CharField(max_length=255)

    TYPE_CHOICES = (
        ("1", "Airport"),
        ("2", "Railway Station"),
        ("3", "Hospital"),
        ("4", "Park"),
        ("5", "Metro"),
        ("6", "Mall"),
        ("7", "Highway"),
        ("8", "Retail / Shopping Mall"),
        ("9", "Business Hub"),
        ("a", "School"),
        ("b", "Public Utility & Connectivity"),
    )
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    distance_km = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        blank=True,
        null=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name}: {self.name}"

    class Meta:
        verbose_name = "Project Amenity or Place"
        verbose_name_plural = "Project Amenities and Places"


class ProjectInquiry(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32)
    message = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"

    class Meta:
        verbose_name = "Project Inquiry"
        verbose_name_plural = "Project Inquiries"
        ordering = ["-created"]
