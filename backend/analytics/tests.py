from django.test import TestCase

from .models import PageAnalytics, PageAnalyticsLog


class PageAnalyticsModelTests(TestCase):

    """Test the PageAnalytics model and visit tracking functionality."""

    def test_record_visit_increments_counter_and_creates_log(self):
        """Verify that recording a visit increments
        the counter and creates a log.
        """
        page = PageAnalytics.objects.create(page="/")

        log = page.record_visit(ip="192.0.2.1")

        page.refresh_from_db()
        self.assertEqual(page.visit, 1)
        self.assertEqual(log.visit, 1)
        self.assertEqual(log.ip, "192.0.2.1")
        self.assertEqual(PageAnalyticsLog.objects.count(), 1)

    def test_each_recorded_visit_increments_counter(self):
        """Verify that each recorded visit increments the
        counter sequentially.
        """
        page = PageAnalytics.objects.create(page="/projects/")

        page.record_visit()
        page.record_visit()

        page.refresh_from_db()
        self.assertEqual(page.visit, 2)
        self.assertEqual(
            list(page.logs.values_list("visit", flat=True)),
            [1, 2],
        )
