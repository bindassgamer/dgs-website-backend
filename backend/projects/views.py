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
from .helper_functions import (
    filter_projects,
    get_id_list
)
from .serializers import (
    PlaceSerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
    ProjectInquirySerializer,
    PersonSearchSerializer,
    ProjectSearchSerializer,
    GalleryPhotoSerializer,
    LocationDropdownSerializer,
    LocationSearchSerializer
)

SEARCH_LIMIT = 4
PAGE_SIZE = 6
GALLERY_PAGE_SIZE = 6


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

    selected_locations = {}
    for level in LOCATION_LEVELS:
        parameter = f"location_{level}"
        ids = get_id_list(request.query_params, parameter)
        if ids:
            selected_locations[parameter] = ids

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
            "selected_locations": selected_locations,
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
        .order_by("pk")[:10]
    )

    people = Person.objects.filter(
        Q(name__icontains=search_term)
        | Q(title__icontains=search_term)
        | Q(description__icontains=search_term)
    ).order_by("order", "pk")

    locations = Location5.objects.filter(
        name__icontains=search_term
    ).order_by("pk")

    context = {"request": request}
    return Response(
        {
            "people": PersonSearchSerializer(
                people, many=True, context=context
            ).data,
            "projects": ProjectSearchSerializer(
                projects, many=True, context=context
            ).data,
            "locations": LocationSearchSerializer(
                locations, many=True, context=context
            ).data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_project_gallery(request):
    """Paginated photos from every project, for the gallery page.

    Optional filters: `project_id` (photos of one project) and `page`.
    """
    photos = ProjectPhoto.objects.exclude(file="").select_related("project")

    project_id = request.query_params.get("project_id", "").strip()
    if project_id:
        if not project_id.isdigit():
            return Response(
                {"error": "project_id must be a project ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        photos = photos.filter(project_id=int(project_id))

    paginator = Paginator(photos.order_by("pk"), GALLERY_PAGE_SIZE)
    try:
        page = paginator.page(request.query_params.get("page", 1))
    except (EmptyPage, PageNotAnInteger):
        return Response(
            {"error": "page must be a valid page number."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = GalleryPhotoSerializer(
        page.object_list,
        many=True,
        context={"request": request},
    )
    next_page = page.next_page_number() if page.has_next() else None
    previous_page = (
        page.previous_page_number() if page.has_previous() else None
    )
    return Response(
        {
            "count": paginator.count,
            "next_page": next_page,
            "previous_page": previous_page,
            "results": serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_location_dropdown(request):
    """Up to 10 Location5 names for a dropdown.

    Optional `search_term` matches the location name.
    """
    search_term = request.query_params.get("search_term", "").strip()
    search_term = search_term[:100]

    locations = Location5.objects.all()
    if search_term:
        locations = locations.filter(name__icontains=search_term)

    locations = locations.only("name").order_by("name", "pk")

    serializer = LocationDropdownSerializer(locations, many=True)
    return Response(
        {"count": len(serializer.data), "results": serializer.data},
        status=status.HTTP_200_OK,
    )
