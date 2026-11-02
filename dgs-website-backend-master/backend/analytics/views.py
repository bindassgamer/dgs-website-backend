from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import PageAnalytics


TRACKED_PAGES = {"home", "aboutUs", "projects", "career"}


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def record_page_visit(request):
    page_name = request.data.get("page")
    if page_name not in TRACKED_PAGES:
        return Response(
            {"page": ["Use home, aboutUs, projects, or career."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    page, _created = PageAnalytics.objects.get_or_create(page=page_name)
    visit = page.record_visit(ip=request.META.get("REMOTE_ADDR"))
    return Response(
        {"page": page_name, "visit": visit.visit},
        status=status.HTTP_201_CREATED,
    )
