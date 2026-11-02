from django.db import models


class Person(models.Model):
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    ROLE_CHOICES = (
        ("1", "Founder"),
        ("2", "Director"),
    )
    image = models.FileField(
        upload_to="peoples/",
        blank=True,
    )
    role = models.CharField(max_length=1, choices=ROLE_CHOICES)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Person"
        verbose_name_plural = "People"
