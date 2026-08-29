from django.urls import path

from .views import (
    CVDetailView,
    CVListCreateView,
    JobApplicationDetailView,
    JobApplicationListCreateView,
    ApplicationNoteListCreateView,
    ApplicationReminderListCreateView,
    InterviewCreateView,
    OfferCreateView,
    ApplicationNoteDetailView,
    ApplicationReminderDetailView,
    InterviewDetailView,
    OfferDetailView,
    CVVersionListView,
)

urlpatterns = [
    path("cv/", CVListCreateView.as_view(), name="cv-list-create"),
    path("cv/<int:pk>/", CVDetailView.as_view(), name="cv-detail"),
    path("cv/<int:cv_id>/versions/", CVVersionListView.as_view(), name="cv-version-list"),
    path("applications/", JobApplicationListCreateView.as_view(), name="job-application-list-create"),
    path("applications/<int:pk>/", JobApplicationDetailView.as_view(), name="job-application-detail"),
    path("applications/<int:application_id>/notes/", ApplicationNoteListCreateView.as_view(), name="application-notes"),
    path("applications/<int:application_id>/notes/<int:pk>/", ApplicationNoteDetailView.as_view(), name="application-note-detail"),
    path("applications/<int:application_id>/reminders/", ApplicationReminderListCreateView.as_view(), name="application-reminders"),
    path("applications/<int:application_id>/reminders/<int:pk>/", ApplicationReminderDetailView.as_view(), name="application-reminder-detail"),
    path("applications/<int:application_id>/interview/", InterviewCreateView.as_view(), name="application-interview"),
    path("applications/<int:application_id>/interview/detail/", InterviewDetailView.as_view(), name="application-interview-detail"),
    path("applications/<int:application_id>/offer/", OfferCreateView.as_view(), name="application-offer"),
    path("applications/<int:application_id>/offer/detail/", OfferDetailView.as_view(), name="application-offer-detail"),
]