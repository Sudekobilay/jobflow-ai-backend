from django.urls import path

from .views import AIMatchView, AISummaryView

urlpatterns = [
    path("summary/", AISummaryView.as_view(), name="ai-summary"),
    path("match/", AIMatchView.as_view(), name="ai-match"),
]
