from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.core.validators import FileExtensionValidator
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from backend.projects.excel_import import build_template, import_workbook

from backend.projects.models import (
    Project,
    ProjectAmenity,
    ProjectAmenityPlace,
    ProjectConfiguration,
    ProjectPhoto,
    ProjectInquiry,
)


class ExcelImportForm(forms.Form):
    file = forms.FileField(
        label="Excel file (.xlsx)",
        validators=[FileExtensionValidator(allowed_extensions=["xlsx"])],
    )


class ProjectConfigurationInline(admin.TabularInline):
    model = ProjectConfiguration
    extra = 0


class ProjectPhotoInline(admin.TabularInline):
    model = ProjectPhoto
    extra = 0


class ProjectAmenityInline(admin.TabularInline):
    model = ProjectAmenity
    extra = 0


class ProjectAmenityPlaceInline(admin.TabularInline):
    model = ProjectAmenityPlace
    extra = 0


class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "bhk_summary",
        "price_budget",
        "project_status",
        "is_featured",
        "created",
        "modified",
    ]
    list_filter = ["project_status", "is_featured"]
    search_fields = ["name", "short_description", "long_description"]
    readonly_fields = ["starting_price"]
    autocomplete_fields = [
        "location_1",
        "location_2",
        "location_3",
        "location_4",
        "location_5",
        "location_6",
    ]
    inlines = [
        ProjectConfigurationInline,
        ProjectPhotoInline,
        ProjectAmenityInline,
        ProjectAmenityPlaceInline,
    ]
    change_list_template = "change_list.html"

    def get_urls(self):
        """Return the default admin URLs along with custom Excel import URLs."""
        custom_urls = [
            path(
                "import-excel/",
                self.admin_site.admin_view(self.import_excel_view),
                name="projects_project_import_excel",
            ),
            path(
                "excel-template/",
                self.admin_site.admin_view(self.excel_template_view),
                name="projects_project_excel_template",
            ),
        ]
        return custom_urls + super().get_urls()

    def _can_import(self, request):
        """Check whether the current user has permission to import projects."""
        return self.has_add_permission(request) and self.has_change_permission(
            request
        )

    def excel_template_view(self, request):
        """Generate and return the Excel import template."""
        if not self._can_import(request):
            raise PermissionDenied
        response = HttpResponse(
            build_template(),
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )
        response["Content-Disposition"] = (
            'attachment; filename="projects_import_template.xlsx"'
        )
        return response

    def import_excel_view(self, request):
        """Handle Excel project imports and
        display validation errors or results.
        """
        if not self._can_import(request):
            raise PermissionDenied
        form = ExcelImportForm(request.POST or None, request.FILES or None)
        errors = []
        if request.method == "POST" and form.is_valid():
            errors, summary = import_workbook(form.cleaned_data["file"])
            if not errors:
                parts = [
                    f"{sheet}: {count} {action}"
                    for (sheet, action), count in sorted(summary.items())
                ]
                messages.success(
                    request, "Import complete. " + "; ".join(parts) + "."
                )
                return redirect(
                    reverse("admin:projects_project_changelist")
                )
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Import projects from Excel",
            "form": form,
            "errors": errors,
        }
        return TemplateResponse(
            request, "import_excel.html", context
        )


class ProjectPhotoAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "created", "modified"]
    search_fields = ["title", "project__name"]


class ProjectAmenityPlaceAdmin(admin.ModelAdmin):
    list_display = ["name", "project", "type", "created", "modified"]
    list_filter = ["type"]
    search_fields = ["name", "project__name"]


class ProjectInquiryAdmin(admin.ModelAdmin):
    list_display = [
        "name", "phone", "email", "project",
        "property_type", "location", "room_type", "created",
    ]
    search_fields = [
        "name",
        "email",
        "phone",
        "property_type",
        "location",
        "room_type"
    ]
    list_filter = ["project"]
    readonly_fields = ["created"]


admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectConfiguration)
admin.site.register(ProjectPhoto, ProjectPhotoAdmin)
admin.site.register(ProjectAmenity)
admin.site.register(ProjectAmenityPlace, ProjectAmenityPlaceAdmin)
admin.site.register(ProjectInquiry, ProjectInquiryAdmin)
