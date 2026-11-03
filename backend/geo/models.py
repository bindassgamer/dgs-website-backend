from django.db import models


class BaseLocation(models.Model):
    name = models.CharField(max_length=64)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


# Six chained location levels, as in the ET ERP geo app: each level points
# at its parent (for example country > state > district > city > area).
class Location1(BaseLocation):
    class Meta:
        verbose_name = "Location1"
        verbose_name_plural = "Location1"


class Location2(BaseLocation):
    location_1 = models.ForeignKey(
        "geo.Location1",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Location2"
        verbose_name_plural = "Location2"


class Location3(BaseLocation):
    location_2 = models.ForeignKey(
        "geo.Location2",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Location3"
        verbose_name_plural = "Location3"


class Location4(BaseLocation):
    location_3 = models.ForeignKey(
        "geo.Location3",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Location4"
        verbose_name_plural = "Location4"


class Location5(BaseLocation):
    location_4 = models.ForeignKey(
        "geo.Location4",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    # Level 5 is the "place" (for example Andheri) shown on the home page.
    image = models.FileField(upload_to="geo/places/", blank=True)

    class Meta:
        verbose_name = "Location5"
        verbose_name_plural = "Location5"


class Location6(BaseLocation):
    location_5 = models.ForeignKey(
        "geo.Location5",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Location6"
        verbose_name_plural = "Location6"
