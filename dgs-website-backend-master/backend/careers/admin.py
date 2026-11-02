from django.contrib import admin

from backend.careers.models import JobApplication


class JobApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "email",
        "mobile_number",
        "job_title",
        "created",
        "modified",
    ]
    search_fields = ["name", "email", "mobile_number", "job_title"]


admin.site.register(JobApplication, JobApplicationAdmin)
