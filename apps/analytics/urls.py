from django.urls import path

from .views import (
    ApplicationAnalyticsView,
    AnalyticsOverviewView,
    SourceAnalyticsView,
    TimelineAnalyticsView,
)

urlpatterns = [
    path("overview/", AnalyticsOverviewView.as_view(), name="analytics-overview"),
    path("applications/", ApplicationAnalyticsView.as_view(), name="analytics-applications"),
    path("sources/", SourceAnalyticsView.as_view(), name="analytics-sources"),
    path("timeline/", TimelineAnalyticsView.as_view(), name="analytics-timeline"),
]