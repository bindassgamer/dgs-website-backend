import re

from rest_framework import serializers

from .models import (
    Job,
    JobApplication,
    JobPoint,
    JobSection,
    JobSubPoint,
)


class DepartmentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class JobSubPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobSubPoint
        fields = ["id", "content"]


class JobPointSerializer(serializers.ModelSerializer):
    sub_points = JobSubPointSerializer(many=True, read_only=True)

    class Meta:
        model = JobPoint
        fields = ["id", "heading", "content", "sub_points"]


class JobSectionSerializer(serializers.ModelSerializer):
    points = JobPointSerializer(many=True, read_only=True)

    class Meta:
        model = JobSection
        fields = ["id", "title", "intro", "points"]


class JobListSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    location = serializers.SerializerMethodField()
    experience = serializers.SerializerMethodField()
    employee_type = serializers.CharField(
        source="get_employee_type_display",
        read_only=True,
    )

    class Meta:
        model = Job
        fields = [
            "id",
            "title",
            "department",
            "location",
            "experience",
            "employee_type",
        ]

    def get_location(self, job):
        name = job.location_name or (
            job.location_5.name if job.location_5 else ""
        )
        return {"id": job.location_5_id, "name": name}

    def get_experience(self, job):
        return f"{job.experience_min:02d}-{job.experience_max:02d} Years"


class JobDetailSerializer(JobListSerializer):
    sections = JobSectionSerializer(many=True, read_only=True)

    class Meta(JobListSerializer.Meta):
        fields = JobListSerializer.Meta.fields + ["sections"]


class JobApplicationSerializer(serializers.ModelSerializer):
    job_id = serializers.PrimaryKeyRelatedField(
        source="job",
        queryset=Job.objects.filter(is_active=True),
    )

    class Meta:
        model = JobApplication
        fields = [
            "id",
            "job_id",
            "name",
            "email",
            "mobile_number",
            "description",
            "resume",
        ]
        read_only_fields = ["id"]

    def validate_mobile_number(self, value):
        digits = re.sub(r"\D", "", value)
        if not 7 <= len(digits) <= 15:
            raise serializers.ValidationError("Enter a valid phone number.")
        return value.strip()

    def create(self, validated_data):
        validated_data["job_title"] = validated_data["job"].title
        return super().create(validated_data)
