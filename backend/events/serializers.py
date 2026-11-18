from zoneinfo import ZoneInfo

from django.utils import timezone
from rest_framework import serializers

from .models import Event

INDIA_TZ = ZoneInfo("Asia/Kolkata")


def ordinal_suffix(day):
    """Return st, nd, rd or th for a day of the month."""
    if 11 <= day <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")


class EventSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()
    day = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "name",
            "start",
            "time",
            "day",
            "date",
            "address",
            "image_url",
        ]

    def _start_in_india(self, event):
        return timezone.localtime(event.start, INDIA_TZ)

    def get_time(self, event):
        """Return the start time, e.g. 02:00pm."""
        return self._start_in_india(event).strftime("%I:%M%p").lower()

    def get_day(self, event):
        """Return the short weekday name, e.g. Sat."""
        return self._start_in_india(event).strftime("%a")

    def get_date(self, event):
        """Return the date, e.g. 07th, Nov 2026."""
        start = self._start_in_india(event)
        suffix = ordinal_suffix(start.day)
        return f"{start.day:02d}{suffix}, {start:%b %Y}"

    def get_image_url(self, event):
        """Return the absolute URL of the event image if available."""
        if not event.image:
            return None
        return self.context["request"].build_absolute_uri(event.image.url)
