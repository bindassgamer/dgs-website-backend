from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Prefetch, Q
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

from backend.geo.models import Location5
from backend.people.models import Person

from .models import LOCATION_LEVELS, Project, ProjectPhoto
from .helper_functions import filter_projects
from .serializers import (
    PlaceSerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
    ProjectInquirySerializer,
    PersonSearchSerializer,
    ProjectSearchSerializer,
)

SEARCH_LIMIT = 4
PAGE_SIZE = 6


class InquiryThrottle(AnonRateThrottle):
    scope = "inquiry"
    rate = "10/hour"


LOCATION_FIELDS = [f"location_{level}" for level in LOCATION_LEVELS]


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
        projects.select_related(*LOCATION_FIELDS)
        .prefetch_related(
            Prefetch(
                "photographs",
                queryset=ProjectPhoto.objects.order_by("pk"),
            ),
            "configurations",
            "amenities",
            "amenities_and_places",
        )
        .order_by("pk"),
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
def get_place_list(request):
    """Places (location 5) that have projects, most projects first.

    `limit` keeps only the top N; `count` is always the total number.
    """
    places = (
        Location5.objects.annotate(project_count=Count("projects"))
        .filter(project_count__gt=0)
        .order_by("-project_count", "name", "pk")
    )
    count = places.count()

    limit = request.query_params.get("limit", "").strip()
    if limit:
        if not limit.isdigit() or int(limit) < 1:
            return Response(
                {"error": "limit must be a positive whole number."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        places = places[: int(limit)]

    serializer = PlaceSerializer(
        places,
        many=True,
        context={"request": request},
    )
    return Response(
        {"count": count, "results": serializer.data},
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
        Project.objects.select_related(*LOCATION_FIELDS).prefetch_related(
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


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def global_search(request):
    search_term = request.query_params.get("search_term", "").strip()
    if not search_term:
        return Response(
            {"error": "search_term is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Reuses the project search logic (name, location, price, BHK).
    projects, filter_error = filter_projects(
        Project.objects.all(),
        {"search_term": search_term},
    )
    if filter_error:
        message, error_status = filter_error
        return Response({"error": message}, status=error_status)

    projects = (
        projects
        .prefetch_related("configurations", "photographs")
        .order_by("pk")[:SEARCH_LIMIT]
    )

    people = Person.objects.filter(
        Q(name__icontains=search_term)
        | Q(title__icontains=search_term)
        | Q(description__icontains=search_term)
    ).order_by("pk")[:SEARCH_LIMIT]

    context = {"request": request}
    return Response(
        {
            "people": PersonSearchSerializer(
                people, many=True, context=context
            ).data,
            "projects": ProjectSearchSerializer(
                projects, many=True, context=context
            ).data,
        },
        status=status.HTTP_200_OK,
    )
