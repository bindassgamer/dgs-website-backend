from django.test import TestCase

from .models import ChannelPartner


class ChannelPartnerModelTests(TestCase):
    def test_created_and_modified_timestamps_are_set(self):
        partner = ChannelPartner.objects.create(
            name="Example Partner",
            number="+911234567890",
            email="partner@example.com",
        )

        self.assertIsNotNone(partner.created)
        self.assertIsNotNone(partner.modified)
