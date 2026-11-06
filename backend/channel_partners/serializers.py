import re

from rest_framework import serializers

from .models import ChannelPartner


class ChannelPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelPartner
        fields = ["id", "name", "number", "email", "type"]
        read_only_fields = ["id"]

    def validate_number(self, value):
        digits = re.sub(r"\D", "", value)
        if not 7 <= len(digits) <= 15:
            raise serializers.ValidationError("Enter a valid phone number.")
        return value.strip()
