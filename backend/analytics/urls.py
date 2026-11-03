from django.urls import path

from .views import record_page_visit


app_name = "analytics"

urlpatterns = [
    path("record-page-visit/", record_page_visit, name="record-page-visit"),
]
