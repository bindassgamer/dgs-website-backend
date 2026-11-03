from django.db import models


class JobApplication(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    mobile_number = models.CharField(max_length=32)
    job_title = models.CharField(max_length=255)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.job_title}"

    class Meta:
        verbose_name = "Job Application"
        verbose_name_plural = "Job Applications"
