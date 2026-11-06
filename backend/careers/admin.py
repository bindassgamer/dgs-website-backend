from django.contrib import admin

from backend.careers.models import (
    Department,
    Job,
    JobApplication,
    JobPoint,
    JobSection,
    JobSubPoint,
)


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "created", "modified"]
    search_fields = ["name"]


class JobSectionInline(admin.TabularInline):
    model = JobSection
    extra = 1


class JobAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "department",
        "location_name",
        "location_5",
        "experience_min",
        "experience_max",
        "employee_type",
        "is_active",
        "created",
        "modified",
    ]
    list_filter = ["department", "employee_type", "is_active"]
    search_fields = ["title", "location_name", "department__name"]
    inlines = [JobSectionInline]


class JobPointInline(admin.StackedInline):
    model = JobPoint
    extra = 1


class JobSectionAdmin(admin.ModelAdmin):
    list_display = ["title", "job", "order"]
    list_filter = ["job"]
    search_fields = ["title", "job__title"]
    inlines = [JobPointInline]


class JobSubPointInline(admin.TabularInline):
    model = JobSubPoint
    extra = 1


class JobPointAdmin(admin.ModelAdmin):
    list_display = ["__str__", "section", "order"]
    list_filter = ["section__job"]
    search_fields = ["heading", "content", "section__title"]
    inlines = [JobSubPointInline]


class JobApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "email",
        "mobile_number",
        "job_title",
        "created",
        "modified",
    ]
    list_filter = ["job"]
    search_fields = ["name", "email", "mobile_number", "job_title"]


admin.site.register(Department, DepartmentAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(JobSection, JobSectionAdmin)
admin.site.register(JobPoint, JobPointAdmin)
admin.site.register(JobApplication, JobApplicationAdmin)
