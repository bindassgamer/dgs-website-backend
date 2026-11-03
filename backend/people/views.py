from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Person


ROLE_VALUES = {label.lower(): value for value, label in Person.ROLE_CHOICES}


def get_image_url(request, person):
    if not person.image:
        return None
    return request.build_absolute_uri(person.image.url)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_people_list(request):
    role = request.query_params.get("role", "").lower()
    if role not in ROLE_VALUES:
        return Response(
            {"error": "A valid role query parameter is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    people = Person.objects.filter(role=ROLE_VALUES[role]).order_by("pk")
    return Response(
        [
            {
                "id": person.pk,
                "name": person.name,
                "title": person.title,
                "description": person.description,
                "image": get_image_url(request, person),
            }
            for person in people
        ],
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_people_details(request):
    person_id = request.query_params.get("person_id")
    try:
        person_id = int(person_id)
    except (TypeError, ValueError):
        return Response(
            {"person_id": ["A valid person ID is required."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    person = get_object_or_404(Person, pk=person_id)
    return Response(
        {
            "name": person.name,
            "title": person.title,
            "description": person.description,
            "image": get_image_url(request, person),
        },
        status=status.HTTP_200_OK,
    )
