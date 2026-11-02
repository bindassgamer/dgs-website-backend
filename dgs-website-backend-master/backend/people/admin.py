from django.contrib import admin

from backend.people.models import Person


class PersonAdmin(admin.ModelAdmin):
    list_display = ["name", "title", "created", "modified"]
    search_fields = ["name", "title"]


admin.site.register(Person, PersonAdmin)
