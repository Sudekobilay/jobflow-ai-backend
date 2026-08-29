from django.urls import path
from .views import (
    CertificateProfileView,
    LanguageProfileView,
    SkillProfileView,
    UserProfileDetailView,
    ProfileCompletionView,
)

urlpatterns = [
    path("me/", UserProfileDetailView.as_view(), name="profile-me"),
    path("me/completion/", ProfileCompletionView.as_view(), name="profile-completion"),
    path("me/skills/", SkillProfileView.as_view(), name="profile-skills"),
    path("me/certificates/", CertificateProfileView.as_view(), name="profile-certificates"),
    path("me/languages/", LanguageProfileView.as_view(), name="profile-languages"),
]