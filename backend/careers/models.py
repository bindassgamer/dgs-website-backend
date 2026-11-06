from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        ordering = ["name"]


class Job(models.Model):
    title = models.CharField(max_length=255)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="jobs",
    )
    # Text shown on the card, e.g. "Andheri West".
    location_name = models.CharField(max_length=255, blank=True)
    # Used only for the Location filter.
    location_5 = models.ForeignKey(
        "geo.Location5",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="jobs",
    )
    experience_min = models.PositiveSmallIntegerField()
    experience_max = models.PositiveSmallIntegerField()
    EMPLOYEE_TYPE_CHOICES = (
        ("1", "Full Time"),
        ("2", "Part Time"),
        ("3", "Contract"),
        ("4", "Internship"),
    )
    employee_type = models.CharField(
        max_length=1,
        choices=EMPLOYEE_TYPE_CHOICES,
        default="1",
    )
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if (
            self.experience_min is not None
            and self.experience_max is not None
            and self.experience_max < self.experience_min
        ):
            raise ValidationError(
                {
                    "experience_max": (
                        "Maximum experience cannot be less than minimum."
                    )
                }
            )

    class Meta:
        verbose_name = "Job"
        verbose_name_plural = "Jobs"
        ordering = ["-created"]


class JobSection(models.Model):
    """e.g. Job Summary, Key Responsibilities, Key Skills Required."""

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    title = models.CharField(max_length=255)
    intro = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"{self.job.title}: {self.title}"

    class Meta:
        verbose_name = "Job Section"
        verbose_name_plural = "Job Sections"
        ordering = ["order", "pk"]


class JobPoint(models.Model):
    """Numbered item. `heading` is optional (used by Responsibilities)."""

    section = models.ForeignKey(
        JobSection,
        on_delete=models.CASCADE,
        related_name="points",
    )
    heading = models.CharField(max_length=500, blank=True)
    content = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.heading or self.content[:50]

    class Meta:
        verbose_name = "Job Point"
        verbose_name_plural = "Job Points"
        ordering = ["order", "pk"]


class JobSubPoint(models.Model):
    """Lettered item (a, b, c) under a point."""

    point = models.ForeignKey(
        JobPoint,
        on_delete=models.CASCADE,
        related_name="sub_points",
    )
    content = models.TextField()
    order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.content[:50]

    class Meta:
        verbose_name = "Job Sub Point"
        verbose_name_plural = "Job Sub Points"
        ordering = ["order", "pk"]


class JobApplication(models.Model):
    job = models.ForeignKey(
        Job,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications",
    )
    name = models.CharField(max_length=255)
    email = models.EmailField()
    mobile_number = models.CharField(max_length=32)
    # Snapshot of the title, so it survives if the job is deleted.
    job_title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    resume = models.FileField(
        upload_to="careers/resumes/",
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx"])
        ],
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.job_title}"

    class Meta:
        verbose_name = "Job Application"
        verbose_name_plural = "Job Applications"
        ordering = ["-created"]