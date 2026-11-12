from django.urls import path

from backend.projects.views import (
    get_place_list,
    get_project_details,
    get_project_list,
    submit_project_inquiry,
    global_search,
    get_project_gallery
)


app_name = "projects"

urlpatterns = [
    path("get-project-list/", get_project_list, name="get-project-list"),
    path("get-place-list/", get_place_list, name="get-place-list"),
    path(
        "get-project-details/",
        get_project_details,
        name="get-project-details",
    ),
    path(
        "submit-project-inquiry/",
        submit_project_inquiry,
        name="submit-project-inquiry",
    ),
    path("global-search/", global_search, name="global-search"),
    path(
        "get-project-gallery/",
        get_project_gallery,
        name="get-project-gallery",
    ),
]
