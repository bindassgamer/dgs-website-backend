from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.throttling import AnonRateThrottle

from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Project, ProjectPhoto
from .helper_functions import filter_projects
from .serializers import (
    ProjectDetailSerializer,
    ProjectListSerializer,
    ProjectInquirySerializer
)


PAGE_SIZE = 6


class InquiryThrottle(AnonRateThrottle):
    rate = "10/hour"


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_project_list(request):
    projects, filter_error = filter_projects(
        Project.objects.all(),
        request.query_params,
    )
    if filter_error:
        message, error_status = filter_error
        return Response(
            {"error": message},
            status=error_status,
        )

    paginator = Paginator(
        projects.prefetch_related(
            Prefetch(
                "photographs",
                queryset=ProjectPhoto.objects.order_by("pk"),
            ),
            "configurations",
        ).order_by("pk"),
        PAGE_SIZE,
    )
    try:
        page = paginator.page(request.query_params.get("page", 1))
    except (EmptyPage, PageNotAnInteger):
        return Response(
            {"error": "page must be a valid page number."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = ProjectListSerializer(
        page.object_list,
        many=True,
        context={"request": request},
    )
    return Response(
        {
            "count": paginator.count,
            "next_page": page.next_page_number() if page.has_next() else None,
            "previous_page": (
                page.previous_page_number() if page.has_previous() else None
            ),
            "results": serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_project_details(request):
    project_id = request.query_params.get("project_id")
    try:
        project_id = int(project_id)
    except (TypeError, ValueError):
        return Response(
            {"project_id": ["A valid project ID is required."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    project = get_object_or_404(
        Project.objects.prefetch_related(
            Prefetch(
                "photographs",
                queryset=ProjectPhoto.objects.order_by("pk"),
            ),
            "configurations",
            "amenities",
            "amenities_and_places",
        ),
        pk=project_id,
    )
    serializer = ProjectDetailSerializer(
        project,
        context={"request": request},
    )
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([InquiryThrottle])
def submit_project_inquiry(request):
    serializer = ProjectInquirySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    inquiry = serializer.save()
    return Response(
        {"id": inquiry.pk, "message": "Thank you, we will contact you soon."},
        status=status.HTTP_201_CREATED,
    )
