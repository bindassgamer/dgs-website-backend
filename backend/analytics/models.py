from django.db import models, transaction
from django.db.models import F


class PageAnalytics(models.Model):
    page = models.CharField(max_length=255, unique=True)
    visit = models.PositiveBigIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def record_visit(self, ip=None):
        with transaction.atomic():
            type(self).objects.filter(pk=self.pk).update(visit=F("visit") + 1)
            self.refresh_from_db(fields=("visit",))
            return self.logs.create(visit=self.visit, ip=ip)

    def __str__(self):
        return self.page

    class Meta:
        verbose_name = "Page Analytics"
        verbose_name_plural = "Page Analytics"


class PageAnalyticsLog(models.Model):
    page = models.ForeignKey(
        PageAnalytics,
        on_delete=models.CASCADE,
        related_name="logs",
    )
    visit = models.PositiveBigIntegerField()
    ip = models.GenericIPAddressField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.page.page}: visit {self.visit}"

    class Meta:
        verbose_name = "Page Analytics Log"
        verbose_name_plural = "Page Analytics Logs"
