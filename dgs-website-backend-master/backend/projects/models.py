from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=255)
    short_description = models.CharField(max_length=500, blank=True)
    long_description = models.TextField(blank=True)
    price_budget = models.CharField(max_length=255)
    location_name = models.CharField(max_length=255, blank=True)
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
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

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
