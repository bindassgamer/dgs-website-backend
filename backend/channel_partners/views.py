from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .serializers import ChannelPartnerSerializer


class ChannelPartnerThrottle(AnonRateThrottle):
    scope = "channel_partner"
    rate = "10/hour"


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([ChannelPartnerThrottle])
def submit_channel_partner(request):
    serializer = ChannelPartnerSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    partner = serializer.save()
    return Response(
        {"id": partner.pk, "message": "Thank you, we will contact you soon."},
        status=status.HTTP_201_CREATED,
    )
