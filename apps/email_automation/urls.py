from django.urls import path

from .views import (
    EmailDraftApprovalView,
    EmailDraftDetailView,
    EmailDraftListView,
    EmailDraftSendView,
    EmailDraftRetryView,
    EmailHistoryView,
    GmailCallbackView,
    GmailConnectView,
    GmailDisconnectView,
)

urlpatterns = [
    path("drafts/", EmailDraftListView.as_view(), name="email-draft-list"),
    path("drafts/<int:pk>/", EmailDraftDetailView.as_view(), name="email-draft-detail"),
    path("drafts/<int:pk>/approve/", EmailDraftApprovalView.as_view(), name="email-draft-approve"),
    path("drafts/<int:pk>/send/", EmailDraftSendView.as_view(), name="email-draft-send"),
    path("drafts/<int:pk>/retry/", EmailDraftRetryView.as_view(), name="email-draft-retry"),
    path("history/", EmailHistoryView.as_view(), name="email-history"),
    path("gmail/connect/", GmailConnectView.as_view(), name="gmail-connect"),
    path("gmail/callback/", GmailCallbackView.as_view(), name="gmail-callback"),
    path("gmail/disconnect/", GmailDisconnectView.as_view(), name="gmail-disconnect"),
]