from urllib.parse import urlencode

from rest_framework import serializers

from .models import (
    Project,
    ProjectAmenity,
    ProjectAmenityPlace,
    ProjectConfiguration,
    ProjectPhoto,
    ProjectInquiry
)
from .helper_functions import format_bhk_counts
import re
from django.conf import settings


class ProjectPhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProjectPhoto
        fields = ["id", "title", "image_url"]

    def get_image_url(self, photo):
        if not photo.file:
            return None
        return self.context["request"].build_absolute_uri(photo.file.url)


class ProjectConfigurationSerializer(serializers.ModelSerializer):
    bhk = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProjectConfiguration
        fields = [
            "id",
            "bhk_count",
            "bhk",
            "carpet_area_sq_ft",
            "bed_count",
            "bathroom_count",
            "image_url",
        ]

    def get_bhk(self, configuration):
        return f"{configuration.bhk_count} BHK"

    def get_image_url(self, configuration):
        if not configuration.image:
            return None
        return self.context["request"].build_absolute_uri(
            configuration.image.url
        )


class ProjectAmenitySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProjectAmenity
        fields = ["id", "name", "image_url"]

    def get_image_url(self, amenity):
        if not amenity.image:
            return None
        return self.context["request"].build_absolute_uri(amenity.image.url)


class ProjectAmenityPlaceSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = ProjectAmenityPlace
        fields = [
            "id",
            "name",
            "category",
            "distance_km",
        ]


class ProjectDetailSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(source="id", read_only=True)
    status = serializers.CharField(
        source="get_project_status_display",
        read_only=True,
    )
    bhk = serializers.SerializerMethodField()
    price = serializers.CharField(source="price_budget", read_only=True)
    image_url = serializers.SerializerMethodField()
    brochure_url = serializers.SerializerMethodField()
    map_url = serializers.SerializerMethodField()
    map_embed_url = serializers.SerializerMethodField()
    map_image_url = serializers.SerializerMethodField()
    photos = ProjectPhotoSerializer(
        source="photographs",
        many=True,
        read_only=True,
    )
    configurations = ProjectConfigurationSerializer(many=True, read_only=True)
    amenities = ProjectAmenitySerializer(many=True, read_only=True)
    neighborhood = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "project_id",
            "name",
            "short_description",
            "long_description",
            "price",
            "status",
            "bhk",
            "location_name",
            "address",
            "latitude",
            "longitude",
            "map_url",
            "map_embed_url",
            "map_image_url",
            "contact_phone",
            "virtual_tour_url",
            "walkthrough_video_url",
            "brochure_url",
            "image_url",
            "photos",
            "configurations",
            "amenities",
            "neighborhood",
            "created",
            "modified",
        ]

    def get_image_url(self, project):
        photos = project.photographs.all()
        photo = photos[0] if photos else None
        if photo is None or not photo.file:
            return None
        return self.context["request"].build_absolute_uri(photo.file.url)

    def get_brochure_url(self, project):
        if not project.brochure:
            return None
        return self.context["request"].build_absolute_uri(
            project.brochure.url
        )

    def get_map_url(self, project):
        if project.latitude is not None and project.longitude is not None:
            query = f"{project.latitude},{project.longitude}"
        else:
            query = project.address or project.location_name
        if not query:
            return None
        return "https://www.google.com/maps/search/?" + urlencode(
            {"api": "1", "query": query}
        )

    def get_map_embed_url(self, project):
        # OpenStreetMap iframe embed: no API key needed.
        if project.latitude is None or project.longitude is None:
            return None
        lat, lon = float(project.latitude), float(project.longitude)
        delta = 0.005
        return "https://www.openstreetmap.org/export/embed.html?" + urlencode(
            {
                "bbox": (
                    f"{lon - delta},{lat - delta},"
                    f"{lon + delta},{lat + delta}"
                ),
                "layer": "mapnik",
                "marker": f"{lat},{lon}",
            }
        )

    def get_map_image_url(self, project):
        # Static map image. Needs GOOGLE_MAPS_API_KEY in settings
        # (restrict the key by HTTP referrer / API in Google Cloud).
        api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", "")
        if (
            not api_key
            or project.latitude is None
            or project.longitude is None
        ):
            return None
        center = f"{project.latitude},{project.longitude}"
        return "https://maps.googleapis.com/maps/api/staticmap?" + urlencode(
            {
                "center": center,
                "zoom": 15,
                "size": "800x400",
                "markers": center,
                "key": api_key,
            }
        )

    def get_bhk(self, project):
        counts = (
            configuration.bhk_count
            for configuration in project.configurations.all()
        )
        return format_bhk_counts(counts)

    def get_neighborhood(self, project):
        places = ProjectAmenityPlaceSerializer(
            project.amenities_and_places.all(),
            many=True,
            context=self.context,
        ).data
        grouped_places = {}
        for place in places:
            grouped_places.setdefault(place["category"], []).append(place)
        return [
            {"category": category, "places": category_places}
            for category, category_places in grouped_places.items()
        ]


class ProjectListSerializer(ProjectDetailSerializer):
    """Same payload as the detail endpoint, so cards need no second call."""

    class Meta(ProjectDetailSerializer.Meta):
        pass


class ProjectInquirySerializer(serializers.ModelSerializer):
    project_id = serializers.PrimaryKeyRelatedField(
        source="project",
        queryset=Project.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ProjectInquiry
        fields = ["id", "project_id", "name", "email", "phone", "message"]
        read_only_fields = ["id"]

    def validate_phone(self, value):
        digits = re.sub(r"\D", "", value)
        if not 7 <= len(digits) <= 15:
            raise serializers.ValidationError("Enter a valid phone number.")
        return value.strip()
