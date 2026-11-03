import re
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from io import BytesIO
from zipfile import BadZipFile

from django.core.exceptions import ValidationError
from django.db import transaction
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from openpyxl.utils.exceptions import InvalidFileException
from openpyxl.worksheet.datavalidation import DataValidation

from .helper_functions import STATUS_VALUES
from .models import (
    Project,
    ProjectAmenity,
    ProjectAmenityPlace,
    ProjectConfiguration,
)

MAX_BHK = 5
CONFIG_FIELDS = ("carpet_area_sq_ft", "bed_count", "bathroom_count")


def field_required(model, field):
    """True when the model field cannot be NULL (so Excel must provide it)."""
    return not model._meta.get_field(field).null


PROJECT_COLUMNS = [
    ("name", True),
    ("price_budget", True),
    ("project_status", True),
    ("is_featured", False),
    ("short_description", False),
    ("long_description", False),
    ("location_name", False),
    ("address", False),
    ("latitude", False),
    ("longitude", False),
    ("contact_phone", False),
    ("virtual_tour_url", False),
    ("walkthrough_video_url", False),
]
for _bhk in range(1, MAX_BHK + 1):
    PROJECT_COLUMNS += [(f"bhk{_bhk}_{field}", False) for field in CONFIG_FIELDS]
PROJECT_COLUMNS.append(("amenities", False))

# sheet name -> [(column, required)]
SHEETS = {
    "Projects": PROJECT_COLUMNS,
    "Places": [
        ("project_name", True),
        ("name", True),
        ("type", True),
        ("distance_km", False),
    ],
}

PLACE_TYPES = {
    label.lower(): value for value, label in ProjectAmenityPlace.TYPE_CHOICES
}
PLACE_TYPES.update(
    {value.lower(): value for value, _ in ProjectAmenityPlace.TYPE_CHOICES}
)
PLACE_TYPES["retail / shopping malls"] = "8"

INSTRUCTIONS = [
    "Projects sheet: one row per project. Places sheet: one row per nearby place.",
    "Projects are matched by name: an existing project with the same name is updated, otherwise it is created.",
    "project_status: Completed Project / OnGoing Project / Upcoming Project (dropdown).",
    "is_featured: Yes / No (dropdown). Featured projects are highlighted on the website.",
    "price_budget: text shown on the website, e.g. '₹ 2.89 Cr Onwards'.",
    "BHK columns: fill bed count and bathroom count for each BHK the project has (carpet area too, if the column header is red); leave a block empty to skip it.",
    "amenities: separate with ; or a new line. Optional description: Name: description.",
    "Places: project_name must match a project name (in the Projects sheet or already saved). Pick type from the dropdown. Red headers are required.",
    "Empty optional cells leave existing values unchanged.",
    "Photos, brochures and images cannot be uploaded via Excel; add them on the project page.",
    "If any row has an error nothing is imported.",
]


def text(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))  # Excel stores 1 as 1.0
    return str(value).strip()


def required(row, column):
    value = text(row.get(column))
    if not value:
        raise ValueError(f"{column} is required")
    return value


def to_decimal(value, label, places=2):
    try:
        number = Decimal(text(value).replace(",", ""))
        if not number.is_finite():
            raise InvalidOperation
        return number.quantize(
            Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP
        )
    except InvalidOperation:
        raise ValueError(f"{label} must be a valid number") from None


def to_int(value, label):
    try:
        number = Decimal(text(value).replace(",", ""))
    except InvalidOperation:
        raise ValueError(f"{label} must be a whole number") from None
    if (
        not number.is_finite()
        or number != number.to_integral_value()
        or number < 0
    ):
        raise ValueError(f"{label} must be a whole number (0 or more)")
    return int(number)


def to_coordinate(value, label, limit):
    number = to_decimal(value, label, places=7)
    if abs(number) > limit:
        raise ValueError(f"{label} must be between -{limit} and {limit}")
    return number


def to_choice(value, mapping, label):
    key = text(value).lower()
    if key not in mapping:
        raise ValueError(f"{label} '{text(value)}' is not valid")
    return mapping[key]


def validation_message(exc):
    if hasattr(exc, "error_dict"):
        return "; ".join(
            f"{field}: {' '.join(messages)}"
            for field, messages in exc.message_dict.items()
        )
    return "; ".join(exc.messages)


def sheet_rows(workbook, sheet_name, errors):
    sheets = {name.strip().lower(): name for name in workbook.sheetnames}
    actual_name = sheets.get(sheet_name.lower())
    if actual_name is None:
        if sheet_name == "Projects":
            errors.append("The 'Projects' sheet is missing.")
        return []
    rows = workbook[actual_name].iter_rows(values_only=True)
    header = next(rows, None) or ()
    headers = [text(cell).lower() for cell in header]
    missing = [
        column
        for column, is_required in SHEETS[sheet_name]
        if is_required and column not in headers
    ]
    if missing:
        errors.append(f"{sheet_name}: missing column(s): {', '.join(missing)}")
        return []
    result = []
    for number, values in enumerate(rows, start=2):
        if all(text(cell) == "" for cell in values):
            continue
        result.append((number, dict(zip(headers, values))))
    return result


def upsert(model, lookup, values):
    instance = model.objects.filter(**lookup).first()
    created = instance is None
    if created:
        instance = model(**lookup)
    for field, value in values.items():
        setattr(instance, field, value)
    instance.full_clean()
    instance.save()
    return instance, created


def find_project(row):
    name = required(row, "project_name")
    matches = list(Project.objects.filter(name=name)[:2])
    if not matches:
        raise ValueError(f"project '{name}' not found")
    if len(matches) > 1:
        raise ValueError(f"more than one project is named '{name}'")
    return matches[0]


def handle_project(row):
    name = required(row, "name")
    if Project.objects.filter(name=name).count() > 1:
        raise ValueError(f"more than one project is named '{name}'")
    values = {
        "price_budget": required(row, "price_budget"),
        "project_status": to_choice(
            required(row, "project_status"), STATUS_VALUES, "project_status"
        ),
    }
    if text(row.get("is_featured")):
        values["is_featured"] = text(row["is_featured"]).lower() in (
            "yes",
            "true",
            "1",
        )
    for field in (
        "short_description",
        "long_description",
        "location_name",
        "address",
        "contact_phone",
        "virtual_tour_url",
        "walkthrough_video_url",
    ):
        if text(row.get(field)):
            values[field] = text(row[field])
    for field, limit in (("latitude", 90), ("longitude", 180)):
        if text(row.get(field)):
            values[field] = to_coordinate(row[field], field, limit)

    project, created = upsert(Project, {"name": name}, values)
    results = [("Projects", created)]

    area_required = field_required(ProjectConfiguration, "carpet_area_sq_ft")
    for bhk in range(1, MAX_BHK + 1):
        columns = [f"bhk{bhk}_{field}" for field in CONFIG_FIELDS]
        if all(text(row.get(column)) == "" for column in columns):
            continue
        area, beds, baths = (text(row.get(column)) for column in columns)
        if not beds or not baths or (area_required and not area):
            needed = (
                "carpet area, bed count and bathroom count"
                if area_required
                else "bed count and bathroom count"
            )
            raise ValueError(f"bhk{bhk}: {needed} are required")
        config_values = {
            "bed_count": to_int(beds, columns[1]),
            "bathroom_count": to_int(baths, columns[2]),
        }
        if area:
            config_values["carpet_area_sq_ft"] = to_decimal(area, columns[0])
        _, created = upsert(
            ProjectConfiguration,
            {"project": project, "bhk_count": bhk},
            config_values,
        )
        results.append(("Configurations", created))

    for item in re.split(r"[;\n]+", text(row.get("amenities"))):
        amenity_name, _, description = item.partition(":")
        amenity_name = amenity_name.strip()
        if not amenity_name:
            continue
        amenity_values = (
            {"description": description.strip()} if description.strip() else {}
        )
        _, created = upsert(
            ProjectAmenity,
            {"project": project, "name": amenity_name},
            amenity_values,
        )
        results.append(("Amenities", created))
    return results


def handle_place(row):
    project = find_project(row)
    values = {"type": to_choice(required(row, "type"), PLACE_TYPES, "type")}
    # for field, limit in (("latitude", 90), ("longitude", 180)):
    #     if text(row.get(field)):
    #         values[field] = to_coordinate(row[field], field, limit)
    #     elif field_required(ProjectAmenityPlace, field):
    #         raise ValueError(f"{field} is required")
    if text(row.get("distance_km")):
        values["distance_km"] = to_decimal(row["distance_km"], "distance_km")
    # if text(row.get("description")):
    #     values["description"] = text(row["description"])
    _, created = upsert(
        ProjectAmenityPlace,
        {"project": project, "name": required(row, "name")},
        values,
    )
    return [("Places", created)]


HANDLERS = (
    ("Projects", handle_project),
    ("Places", handle_place),
)


def import_workbook(uploaded_file):
    """Returns (errors, summary). Nothing is saved if errors is non-empty."""
    try:
        workbook = load_workbook(uploaded_file, read_only=True, data_only=True)
    except (InvalidFileException, BadZipFile):
        return ["The file is not a valid .xlsx workbook."], Counter()

    errors, summary = [], Counter()
    failed_projects = set()
    with transaction.atomic():
        for sheet_name, handler in HANDLERS:
            for number, row in sheet_rows(workbook, sheet_name, errors):
                # A project that failed is already reported; don't repeat
                # "project not found" for each of its places.
                if (
                    sheet_name == "Places"
                    and text(row.get("project_name")) in failed_projects
                ):
                    continue
                try:
                    results = handler(row)
                except (ValueError, ValidationError) as exc:
                    message = (
                        validation_message(exc)
                        if isinstance(exc, ValidationError)
                        else str(exc)
                    )
                    errors.append(f"{sheet_name} row {number}: {message}")
                    if sheet_name == "Projects":
                        failed_projects.add(text(row.get("name")))
                else:
                    for label, created in results:
                        summary[(label, "created" if created else "updated")] += 1
        if errors:
            transaction.set_rollback(True)
    return errors, summary


def build_template():
    workbook = Workbook()
    info = workbook.active
    info.title = "Instructions"
    for line in INSTRUCTIONS:
        info.append([line])
    info.column_dimensions["A"].width = 120

    for sheet_name, columns in SHEETS.items():
        sheet = workbook.create_sheet(sheet_name)
        sheet.append([column for column, _ in columns])
        for index, (column, is_required) in enumerate(columns, start=1):
            cell = sheet.cell(row=1, column=index)
            cell.font = Font(bold=True, color="C00000" if is_required else "000000")
            sheet.column_dimensions[get_column_letter(index)].width = max(
                16, len(column) + 4
            )
        sheet.freeze_panes = "A2"

    def add_dropdown(sheet_name, column, labels):
        index = [c for c, _ in SHEETS[sheet_name]].index(column) + 1
        letter = get_column_letter(index)
        validation = DataValidation(
            type="list", formula1='"' + ",".join(labels) + '"', allow_blank=True
        )
        workbook[sheet_name].add_data_validation(validation)
        validation.add(f"{letter}2:{letter}1000")

    add_dropdown(
        "Projects",
        "project_status",
        [label for _, label in Project.PROJECT_STATUS_CHOICES],
    )
    add_dropdown("Projects", "is_featured", ["Yes", "No"])
    add_dropdown(
        "Places", "type", [label for _, label in ProjectAmenityPlace.TYPE_CHOICES]
    )

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
