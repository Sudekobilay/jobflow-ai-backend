from django.urls import path

from .views import (
    AICVAnalyzeView,
    AICoverLetterView,
    AIMatchView,
    AISummaryView,
    CVAnalysisDetailView,
    CVAnalysisListView,
    AssistantChatView,
    AssistantConversationDetailView,
    AssistantConversationListView,
    JobMatchDetailView,
    JobMatchListView,
    AIUsageReportView,
)

urlpatterns = [
    path("summary/", AISummaryView.as_view(), name="ai-summary"),
    path("match/", AIMatchView.as_view(), name="ai-match"),
    path("matches/", JobMatchListView.as_view(), name="ai-match-list"),
    path("matches/<int:pk>/", JobMatchDetailView.as_view(), name="ai-match-detail"),
    path("usage/", AIUsageReportView.as_view(), name="ai-usage-report"),
    path("cv/analyze/", AICVAnalyzeView.as_view(), name="ai-cv-analyze"),
    path("cv/analyses/", CVAnalysisListView.as_view(), name="ai-cv-analysis-list"),
    path("cv/analyses/<int:pk>/", CVAnalysisDetailView.as_view(), name="ai-cv-analysis-detail"),
    path("assistant/", AssistantChatView.as_view(), name="ai-assistant"),
    path("assistant/conversations/", AssistantConversationListView.as_view(), name="ai-assistant-conversations"),
    path("assistant/conversations/<int:pk>/", AssistantConversationDetailView.as_view(), name="ai-assistant-conversation-detail"),
    path("cover-letter/", AICoverLetterView.as_view(), name="ai-cover-letter"),
]
