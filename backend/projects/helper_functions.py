from decimal import Decimal, InvalidOperation
import re

from django.db.models import CharField, Q, QuerySet
from django.db.models.functions import Cast
from rest_framework import status

from .models import Project


STATUS_VALUES = {
    label.lower(): value for value, label in Project.PROJECT_STATUS_CHOICES
}
STATUS_VALUES.update(
    {value.lower(): value for value, _label in Project.PROJECT_STATUS_CHOICES}
)
STATUS_VALUES.update(
    {
        "completed": "1",
        "ongoing": "2",
        "upcoming": "3",
    }
)


def format_bhk_counts(counts):
    ordered_counts = sorted(counts)
    if not ordered_counts:
        return ""
    if len(ordered_counts) == 1:
        return f"{ordered_counts[0]} BHK"
    return (
        f"{', '.join(map(str, ordered_counts[:-1]))} "
        f"& {ordered_counts[-1]} BHK"
    )


def filter_projects(queryset: QuerySet, query_params):
    status_filter = query_params.get("status", "").strip().lower()
    if status_filter:
        project_status = STATUS_VALUES.get(status_filter)
        if project_status is None:
            return None, (
                "status must be Completed, OnGoing, or Upcoming.",
                status.HTTP_400_BAD_REQUEST,
            )
        queryset = queryset.filter(project_status=project_status)

    location = query_params.get("location", "").strip()
    if location:
        queryset = queryset.filter(
            Q(location_name__icontains=location)
            | Q(address__icontains=location)
        )

    for parameter, lookup in (
        ("min_price", "price_budget__gte"),
        ("max_price", "price_budget__lte"),
    ):
        value = query_params.get(parameter, "").strip()
        if value:
            try:
                price = Decimal(value)
            except InvalidOperation:
                return None, (
                    f"{parameter} must be a valid number.",
                    status.HTTP_400_BAD_REQUEST,
                )
            if not price.is_finite():
                return None, (
                    f"{parameter} must be a finite number.",
                    status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(**{lookup: price})

    bhk = query_params.get("bhk", "").strip()
    if bhk:
        try:
            bhk_count = int(bhk)
        except ValueError:
            return None, (
                "bhk must be a positive whole number.",
                status.HTTP_400_BAD_REQUEST,
            )
        if bhk_count < 1:
            return None, (
                "bhk must be a positive whole number.",
                status.HTTP_400_BAD_REQUEST,
            )
        queryset = queryset.filter(configurations__bhk_count=bhk_count)

    search_term = query_params.get("search_term", "").strip()
    if search_term:
        search_filter = (
            Q(name__icontains=search_term)
            | Q(location_name__icontains=search_term)
            | Q(address__icontains=search_term)
            | Q(price_budget_text__icontains=search_term)
        )
        bhk_numbers = set()
        if re.search(r"\bbhk\b", search_term, re.IGNORECASE):
            bhk_numbers = {
                int(number)
                for number in re.findall(r"\d+", search_term)
                if int(number) > 0
            }
        elif search_term.isdigit() and int(search_term) > 0:
            bhk_numbers.add(int(search_term))
        if bhk_numbers:
            search_filter |= Q(configurations__bhk_count__in=bhk_numbers)

        price_match = re.fullmatch(
            r"(?:₹\s*)?([\d,]+(?:\.\d+)?)\s*"
            r"(cr|crore|crores|lac|lacs|lakh|lakhs)?",
            search_term,
            re.IGNORECASE,
        )
        if price_match:
            amount = Decimal(price_match.group(1).replace(",", ""))
            scale = (price_match.group(2) or "").lower()
            if scale in {"cr", "crore", "crores"}:
                amount *= Decimal("10000000")
            elif scale in {"lac", "lacs", "lakh", "lakhs"}:
                amount *= Decimal("100000")
            search_filter |= Q(price_budget=amount)

        queryset = queryset.annotate(
            price_budget_text=Cast("price_budget", output_field=CharField())
        ).filter(search_filter)

    return queryset.distinct(), None
