from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


admin.site.site_header = "DGS IT Backend"


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/analytics/", include("backend.analytics.urls")),
    path("api/people/", include("backend.people.urls")),
    path("api/projects/", include("backend.projects.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
