from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.decorators import parser_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from backend.geo.models import Location5

from .models import Department, Job
from .serializers import (
    JobApplicationSerializer,
    JobDetailSerializer,
    JobListSerializer,
)


PAGE_SIZE = 10

EXPERIENCE_RANGES = [
    ("0-2", "0-2 Years"),
    ("3-5", "3-5 Years"),
    ("6-10", "6-10 Years"),
    ("10-50", "10+ Years"),
]


class JobApplicationThrottle(AnonRateThrottle):
    scope = "job_application"
    rate = "10/hour"


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_job_filters(request):
    active = Q(jobs__is_active=True)
    departments = (
        Department.objects.annotate(job_count=Count("jobs", filter=active))
        .filter(job_count__gt=0)
        .order_by("name")
    )
    locations = (
        Location5.objects.annotate(job_count=Count("jobs", filter=active))
        .filter(job_count__gt=0)
        .order_by("-job_count", "name", "pk")
    )
    return Response(
        {
            "department": [
                {"id": d.pk, "name": d.name, "job_count": d.job_count}
                for d in departments
            ],
            "location": [
                {"id": l.pk, "name": l.name, "job_count": l.job_count}
                for l in locations
            ],
            "experience": [
                {"value": value, "label": label}
                for value, label in EXPERIENCE_RANGES
            ],
            "employee_type": [
                {"value": value, "label": label}
                for value, label in Job.EMPLOYEE_TYPE_CHOICES
            ],
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_job_list(request):
    params = request.query_params
    jobs = Job.objects.filter(is_active=True)

    # department=1,2 and location=12,15 (comma-separated ids, OR within a group)
    for parameter, lookup in (
        ("department", "department_id__in"),
        ("location", "location_5_id__in"),
    ):
        value = params.get(parameter, "").strip()
        if value:
            ids = value.split(",")
            if not all(item.strip().isdigit() for item in ids):
                return Response(
                    {"error": f"{parameter} must be comma-separated IDs."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            jobs = jobs.filter(**{lookup: [int(item) for item in ids]})

    employee_types = params.get("employee_type", "").strip()
    if employee_types:
        valid = {value for value, _label in Job.EMPLOYEE_TYPE_CHOICES}
        types = [item.strip() for item in employee_types.split(",")]
        if not set(types) <= valid:
            return Response(
                {"error": "employee_type has an invalid value."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        jobs = jobs.filter(employee_type__in=types)

    # experience=0-2,6-10: a job matches when its range overlaps (OR).
    experience = params.get("experience", "").strip()
    if experience:
        experience_filter = Q()
        for item in experience.split(","):
            low, _, high = item.strip().partition("-")
            if not (low.isdigit() and high.isdigit()) or int(low) > int(high):
                return Response(
                    {"error": "experience must look like 3-5."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            experience_filter |= Q(
                experience_min__lte=int(high),
                experience_max__gte=int(low),
            )
        jobs = jobs.filter(experience_filter)

    search_term = params.get("search_term", "").strip()
    if search_term:
        jobs = jobs.filter(
            Q(title__icontains=search_term)
            | Q(department__name__icontains=search_term)
            | Q(location_name__icontains=search_term)
            | Q(location_5__name__icontains=search_term)
        )

    paginator = Paginator(
        jobs.select_related("department", "location_5").order_by("-created", "pk"),
        PAGE_SIZE,
    )
    try:
        page = paginator.page(params.get("page", 1))
    except (EmptyPage, PageNotAnInteger):
        return Response(
            {"error": "page must be a valid page number."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = JobListSerializer(page.object_list, many=True)
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
def get_job_details(request):
    job_id = request.query_params.get("job_id")
    try:
        job_id = int(job_id)
    except (TypeError, ValueError):
        return Response(
            {"job_id": ["A valid job ID is required."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    job = get_object_or_404(
        Job.objects.filter(is_active=True)
        .select_related("department", "location_5")
        .prefetch_related("sections__points__sub_points"),
        pk=job_id,
    )
    return Response(JobDetailSerializer(job).data, status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@throttle_classes([JobApplicationThrottle])
def submit_job_application(request):
    serializer = JobApplicationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    application = serializer.save()
    return Response(
        {
            "id": application.pk,
            "message": "Thank you, we will contact you soon.",
        },
        status=status.HTTP_201_CREATED,
    )
