from django.core.validators import FileExtensionValidator
from django.db import models


class Event(models.Model):
    name = models.CharField(max_length=255)
    # Stored in UTC. The admin shows and accepts it in TIME_ZONE (Asia/Kolkata).
    start = models.DateTimeField(help_text="Event date and time (India time).")
    address = models.TextField()
    image = models.FileField(
        upload_to="events/images/",
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png", "webp"]
            )
        ],
    )
    is_published = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.start:%d %b %Y})"

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"
        ordering = ["start"]
        indexes = [models.Index(fields=["start"])]
