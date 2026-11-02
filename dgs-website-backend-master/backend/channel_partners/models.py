from django.db import models


class ChannelPartner(models.Model):
    name = models.CharField(max_length=255)
    number = models.CharField(max_length=32)
    email = models.EmailField()
    type = models.CharField(max_length=100, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Channel Partner"
        verbose_name_plural = "Channel Partners"
