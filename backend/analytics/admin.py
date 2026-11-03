from django.contrib import admin

from backend.analytics.models import PageAnalytics, PageAnalyticsLog


class PageAnalyticsLogInline(admin.TabularInline):
    model = PageAnalyticsLog
    extra = 0
    readonly_fields = ["visit", "ip", "date"]
    can_delete = False


class PageAnalyticsAdmin(admin.ModelAdmin):
    list_display = ["page", "visit", "created", "modified"]
    search_fields = ["page"]
    inlines = [PageAnalyticsLogInline]


class PageAnalyticsLogAdmin(admin.ModelAdmin):
    list_display = [
        "page",
        "visit",
        "ip",
        "date",
        "created",
        "modified",
    ]
    list_filter = ["date"]
    search_fields = ["page__page", "ip"]
    readonly_fields = ["page", "visit", "ip", "date"]


admin.site.register(PageAnalytics, PageAnalyticsAdmin)
admin.site.register(PageAnalyticsLog, PageAnalyticsLogAdmin)
