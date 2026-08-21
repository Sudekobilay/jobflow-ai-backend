import re

from django.db.models import Q
from rest_framework import generics, permissions

from .models import Job
from .serializers import JobSerializer
from drf_spectacular.utils import extend_schema

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
        queryset = Job.objects.all().order_by("-created_at")
        params = self.request.query_params

        search = params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(company__icontains=search) | Q(description__icontains=search)
            )

        location = params.get("location")
        if location:
            queryset = queryset.filter(location__icontains=location)

        is_remote = params.get("is_remote")
        if is_remote is not None:
            queryset = queryset.filter(is_remote=is_remote.lower() in {"1", "true", "yes", "on"})

        min_salary = self._parse_salary(params.get("min_salary"))
        if min_salary is not None:
            queryset = queryset.filter(
                salary__isnull=False,
            )
            filtered = []
            for job in queryset:
                job_salary = self._parse_salary(job.salary)
                if job_salary is not None and job_salary >= min_salary:
                    filtered.append(job.pk)
            queryset = queryset.filter(pk__in=filtered)

        max_salary = self._parse_salary(params.get("max_salary"))
        if max_salary is not None:
            queryset = queryset.filter(
                salary__isnull=False,
            )
            filtered = []
            for job in queryset:
                job_salary = self._parse_salary(job.salary)
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
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Job.objects.all()
