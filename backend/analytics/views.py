import ipaddress

from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, BaseThrottle

from .models import PageAnalytics


TRACKED_PAGES = {"home", "aboutUs", "projects", "career", "channel_partner"}


class PageVisitThrottle(AnonRateThrottle):

    """Limit anonymous page visit requests."""

    scope = "page_visit"
    rate = "120/hour"


def get_client_ip(request):
    """Return the validated client IP address or None if invalid."""
    try:
        return str(ipaddress.ip_address(BaseThrottle().get_ident(request)))
    except ValueError:
        return None


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([PageVisitThrottle])
def record_page_visit(request):
    """Record a page visit and return its updated visit count."""
    page_name = request.data.get("page")
    if page_name not in TRACKED_PAGES:
        return Response(
            {"page": [
                "Use home, aboutUs, projects, channel_partner or career."
                ]
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    page, _created = PageAnalytics.objects.get_or_create(page=page_name)
    visit = page.record_visit(ip=get_client_ip(request))
    return Response(
        {"page": page_name, "visit": visit.visit},
        status=status.HTTP_201_CREATED,
    )
