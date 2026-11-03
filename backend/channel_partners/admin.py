from django.contrib import admin

from backend.channel_partners.models import ChannelPartner


class ChannelPartnerAdmin(admin.ModelAdmin):
    list_display = ["name", "number", "email", "type", "created"]
    list_filter = ["type", "created"]
    search_fields = ["name", "number", "email"]


admin.site.register(ChannelPartner, ChannelPartnerAdmin)
