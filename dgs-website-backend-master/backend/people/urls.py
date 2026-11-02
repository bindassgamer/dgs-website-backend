from django.urls import path

from backend.people.views import get_people_details, get_people_list


app_name = "people"

urlpatterns = [
    path("get-people-list/", get_people_list, name="get-people-list"),
    path(
        "get-people-details/",
        get_people_details,
        name="get-people-details",
    ),
]
