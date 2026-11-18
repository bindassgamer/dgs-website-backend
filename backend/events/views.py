from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Event
from .serializers import EventSerializer


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_upcoming_events(request):
    """Return upcoming published events, soonest first."""
    events = Event.objects.filter(
        is_published=True,
        start__gte=timezone.now(),
    ).order_by("start", "pk")

    serializer = EventSerializer(
        events,
        many=True,
        context={"request": request},
    )
    return Response(
        {"count": len(serializer.data), "results": serializer.data},
        status=status.HTTP_200_OK,
    )
