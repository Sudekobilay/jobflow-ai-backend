import re

from django.db.models import IntegerField, OuterRef, Q, Subquery
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Job, JobSyncRun
from .serializers import JobSerializer
from drf_spectacular.utils import extend_schema


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user or request.user.is_staff

@extend_schema(
    summary="İş listesi",
    description="Tüm iş ilanlarını listeler.",
    tags=["Jobs"],
)
class JobListCreateView(generics.ListCreateAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def _parse_salary(value):
        if value in (None, ""):
            return None
        cleaned = re.sub(r"[^0-9.-]", "", str(value))
        if cleaned in ("", "-", "."):
            return None
        try:
            return int(float(cleaned))
        except (TypeError, ValueError):
            return None

    def get_queryset(self):
        queryset = Job.objects.filter(is_active=True).order_by("-created_at")
        params = self.request.query_params

        match_cv_id = params.get("match_cv_id")
        if match_cv_id:
            from apps.ai_services.models import JobMatch

            latest_match = JobMatch.objects.filter(
                user=self.request.user,
                cv_id=match_cv_id,
                job_id=OuterRef("pk"),
            ).order_by("-created_at").values("match_score")[:1]
            queryset = queryset.annotate(
                match_score=Subquery(latest_match, output_field=IntegerField())
            ).filter(match_score__isnull=False).order_by("-match_score", "-created_at")

        search = params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(company__icontains=search) | Q(description__icontains=search)
            )

        location = params.get("location")
        if location:
            queryset = queryset.filter(location__icontains=location)

        source = params.get("source")
        if source:
            queryset = queryset.filter(source=source)

        technology = params.get("technology")
        if technology:
            queryset = queryset.filter(technologies__icontains=technology)

        experience_level = params.get("experience_level")
        if experience_level:
            queryset = queryset.filter(experience_level__iexact=experience_level)

        is_remote = params.get("is_remote")
        if is_remote is not None:
            queryset = queryset.filter(is_remote=is_remote.lower() in {"1", "true", "yes", "on"})

        min_salary = self._parse_salary(params.get("min_salary"))
        if min_salary is not None:
            filtered = []
            for job in queryset:
                job_salary = job.salary_min or self._parse_salary(job.salary)
                if job_salary is not None and job_salary >= min_salary:
                    filtered.append(job.pk)
            queryset = queryset.filter(pk__in=filtered)

        max_salary = self._parse_salary(params.get("max_salary"))
        if max_salary is not None:
            filtered = []
            for job in queryset:
                job_salary = job.salary_max or job.salary_min or self._parse_salary(job.salary)
                if job_salary is not None and job_salary <= max_salary:
                    filtered.append(job.pk)
            queryset = queryset.filter(pk__in=filtered)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(
    summary="İş detayları",
    description="Belirli bir iş ilanının detaylarını gösterir.",
    tags=["Jobs"],
)
class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Job.objects.all()


class JobSyncHealthView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        runs = JobSyncRun.objects.order_by("-started_at")[:20]
        return Response([
            {"source": run.source, "status": run.status, "fetched_count": run.fetched_count,
             "created_count": run.created_count, "updated_count": run.updated_count,
             "error_message": run.error_message, "started_at": run.started_at,
             "finished_at": run.finished_at}
            for run in runs
        ])
