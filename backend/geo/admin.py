from django.contrib import admin

from backend.geo.models import (
    Location1,
    Location2,
    Location3,
    Location4,
    Location5,
    Location6,
)


class Location1Admin(admin.ModelAdmin):
    list_display = ["id", "name", "created", "modified"]
    search_fields = ["name"]


class Location2Admin(admin.ModelAdmin):
    list_display = ["id", "name", "location_1", "created", "modified"]
    list_filter = ["location_1"]
    search_fields = ["name"]
    autocomplete_fields = ["location_1"]


class Location3Admin(admin.ModelAdmin):
    list_display = ["id", "name", "location_2", "created", "modified"]
    list_filter = ["location_2"]
    search_fields = ["name"]
    autocomplete_fields = ["location_2"]


class Location4Admin(admin.ModelAdmin):
    list_display = ["id", "name", "location_3", "created", "modified"]
    list_filter = ["location_3"]
    search_fields = ["name"]
    autocomplete_fields = ["location_3"]


class Location5Admin(admin.ModelAdmin):
    list_display = ["id", "name", "location_4", "created", "modified"]
    list_filter = ["location_4"]
    search_fields = ["name"]
    autocomplete_fields = ["location_4"]


class Location6Admin(admin.ModelAdmin):
    list_display = ["id", "name", "location_5", "created", "modified"]
    list_filter = ["location_5"]
    search_fields = ["name"]
    autocomplete_fields = ["location_5"]


admin.site.register(Location1, Location1Admin)
admin.site.register(Location2, Location2Admin)
admin.site.register(Location3, Location3Admin)
admin.site.register(Location4, Location4Admin)
admin.site.register(Location5, Location5Admin)
admin.site.register(Location6, Location6Admin)
