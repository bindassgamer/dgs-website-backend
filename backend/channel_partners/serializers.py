import re

from rest_framework import serializers

from .models import ChannelPartner


class ChannelPartnerSerializer(serializers.ModelSerializer):

    """Serialize ChannelPartner model data and validate input fields."""

    class Meta:

        """Define the model fields and read-only fields for the serializer."""

        model = ChannelPartner
        fields = ["id", "name", "number", "email", "type"]
        read_only_fields = ["id"]

    def validate_number(self, value):
        """Validate the phone number by checking that it contains
        7 to 15 digits.
        """
        digits = re.sub(r"\D", "", value)
        if not 7 <= len(digits) <= 15:
            raise serializers.ValidationError("Enter a valid phone number.")
        return value.strip()
