from rest_framework import generics, permissions

from .models import CV, JobApplication
from .serializers import CVSerializer, JobApplicationSerializer
from drf_spectacular.utils import extend_schema

@extend_schema(
    summary="CV Listeleme ve Oluşturma",
    description="Kullanıcının CV'lerini listeler veya yeni bir CV oluşturur.",
    tags=["Applications"],
)
class CVListCreateView(generics.ListCreateAPIView):
    serializer_class = CVSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CV.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(
    summary="CV Detayı",
    description="Kullanıcının belirli bir CV'sini görüntüler, günceller veya siler.",
    tags=["Applications"],
)
class CVDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CVSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CV.objects.filter(user=self.request.user)


@extend_schema(
    summary="İş Başvurusu Listeleme ve Oluşturma",
    description="Kullanıcının iş başvurularını listeler veya yeni bir iş başvurusu oluşturur.",
    tags=["Applications"],
)
class JobApplicationListCreateView(generics.ListCreateAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JobApplication.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(
    summary="İş Başvurusu Detayı",
    description="Kullanıcının belirli bir iş başvurusunu görüntüler, günceller veya siler.",
    tags=["Applications"],
)
class JobApplicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JobApplication.objects.filter(user=self.request.user)
