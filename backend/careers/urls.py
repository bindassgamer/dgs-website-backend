from django.urls import path

from backend.careers.views import (
    get_job_details,
    get_job_filters,
    get_job_list,
    submit_job_application,
)


app_name = "careers"

urlpatterns = [
    path("get-job-filters/", get_job_filters, name="get-job-filters"),
    path("get-job-list/", get_job_list, name="get-job-list"),
    path("get-job-details/", get_job_details, name="get-job-details"),
    path(
        "submit-job-application/",
        submit_job_application,
        name="submit-job-application",
    ),
]
