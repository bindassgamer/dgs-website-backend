from decimal import Decimal, InvalidOperation
import re

from django.db.models import Q, QuerySet
from rest_framework import status

from .models import LOCATION_LEVELS, Project
from .price import parse_price

BHK_WORD = re.compile(r"bhk", re.IGNORECASE)
SMALL_NUMBER = re.compile(r"(?<!\d)\d{1,2}(?!\d)")
DIGIT_LETTER_GAP = re.compile(r"(?<=\d)(?=[a-zA-Z])")

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


def extract_bhk_numbers(search_term):
    """Return BHK counts from terms like '1 bhk', '1bhk', '2-bhk',
    '2 & 3 BHK' or a bare '2'.
    """
    if BHK_WORD.search(search_term):
        numbers = SMALL_NUMBER.findall(search_term)
    elif search_term.isdigit() and len(search_term) <= 2:
        numbers = [search_term]
    else:
        numbers = []
    return {int(number) for number in numbers if int(number) > 0}


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


def location_q(term):
    """Match a place name in the free-text fields or any location level."""
    query = Q(location_name__icontains=term) | Q(address__icontains=term)
    for level in LOCATION_LEVELS:
        query |= Q(**{f"location_{level}__name__icontains": term})
    return query


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

    if query_params.get("featured", "").strip().lower() in ("true", "1"):
        queryset = queryset.filter(is_featured=True)

    location = query_params.get("location", "").strip()
    if location:
        queryset = queryset.filter(location_q(location))

    for level in LOCATION_LEVELS:
        parameter = f"location_{level}"
        ids = get_id_list(query_params, parameter)
        if ids is None:
            return None, (
                f"{parameter} must be a location ID or a list of location IDs.",
                status.HTTP_400_BAD_REQUEST,
            )
        if ids:
            queryset = queryset.filter(**{f"{parameter}_id__in": ids})

    for parameter, lookup in (
        ("min_price", "starting_price__gte"),
        ("max_price", "starting_price__lte"),
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

    search_term = " ".join(query_params.get("search_term", "").split())
    if search_term:
        search_filter = (
            Q(name__icontains=search_term)
            | location_q(search_term)
            | Q(price_budget__icontains=search_term)
        )

        bhk_numbers = extract_bhk_numbers(search_term)
        if bhk_numbers:
            search_filter |= Q(configurations__bhk_count__in=bhk_numbers)

        amount = parse_price(search_term)
        if amount is None:
            amount = parse_price(DIGIT_LETTER_GAP.sub(" ", search_term))
        if amount is not None:
            search_filter |= Q(starting_price=amount)

        queryset = queryset.filter(search_filter)

    return queryset.distinct(), None


def parse_id_list(raw_values):
    """Turn ['2,9', '1', '4'] into [2, 9, 1, 4].
    Returns None if any part is invalid.
    """
    ids = []
    for raw in raw_values:
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            if not part.isdigit():
                return None
            ids.append(int(part))
    return ids


def get_id_list(query_params, parameter):
    """Read repeated keys (a=1&a=2), the [] form (a[]=1),
    and comma lists (a=1,2).
    Works with a Django QueryDict and with a plain dict.
    """
    raw_values = []
    for key in (parameter, f"{parameter}[]"):
        if hasattr(query_params, "getlist"):
            raw_values.extend(query_params.getlist(key))
            continue
        value = query_params.get(key)
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            raw_values.extend(str(item) for item in value)
        else:
            raw_values.append(str(value))
    return parse_id_list(raw_values)
