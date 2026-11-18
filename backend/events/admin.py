from django.contrib import admin

from backend.events.models import Event


class EventAdmin(admin.ModelAdmin):
    list_display = ["name", "start", "is_published", "created", "modified"]
    list_filter = ["is_published"]
    search_fields = ["name", "address"]
    date_hierarchy = "start"


admin.site.register(Event, EventAdmin)
