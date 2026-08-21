from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("", RedirectView.as_view(url='/api/docs/', permanent=False)),
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.authentication.urls")),
    path("api/profiles/", include("apps.profiles.urls")),
    path("api/", include("apps.applications.urls")),
    path("api/jobs/", include("apps.jobs.urls")),
    path("api/ai/", include("apps.ai_services.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]