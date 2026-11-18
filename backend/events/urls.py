from django.urls import path

from backend.events.views import get_upcoming_events


app_name = "events"

urlpatterns = [
    path(
        "get-upcoming-events/",
        get_upcoming_events,
        name="get-upcoming-events",
    ),
]
