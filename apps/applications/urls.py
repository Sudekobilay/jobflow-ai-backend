from django.urls import path

from .views import (
    CVDetailView,
    CVListCreateView,
    JobApplicationDetailView,
    JobApplicationListCreateView,
)

urlpatterns = [
    path("cv/", CVListCreateView.as_view(), name="cv-list-create"),
    path("cv/<int:pk>/", CVDetailView.as_view(), name="cv-detail"),
    path("applications/", JobApplicationListCreateView.as_view(), name="job-application-list-create"),
    path("applications/<int:pk>/", JobApplicationDetailView.as_view(), name="job-application-detail"),
]