from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions

from .models import ApplicationNote, ApplicationReminder, CV, CVVersion, Interview, JobApplication, Offer
from .serializers import ApplicationNoteSerializer, ApplicationReminderSerializer, CVSerializer, CVVersionSerializer, InterviewSerializer, JobApplicationSerializer, OfferSerializer
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


class CVVersionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CVVersionSerializer

    def get_queryset(self):
        return CVVersion.objects.filter(cv_id=self.kwargs["cv_id"], cv__user=self.request.user)


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


class ApplicationChildMixin:
    model = None

    def get_queryset(self):
        return self.model.objects.filter(application__user=self.request.user)

    def perform_create(self, serializer):
        application = get_object_or_404(JobApplication, pk=self.kwargs["application_id"], user=self.request.user)
        serializer.save(application=application)


class ApplicationNoteListCreateView(ApplicationChildMixin, generics.ListCreateAPIView):
    model = ApplicationNote
    serializer_class = ApplicationNoteSerializer
    permission_classes = [permissions.IsAuthenticated]


class ApplicationReminderListCreateView(ApplicationChildMixin, generics.ListCreateAPIView):
    model = ApplicationReminder
    serializer_class = ApplicationReminderSerializer
    permission_classes = [permissions.IsAuthenticated]


class InterviewCreateView(ApplicationChildMixin, generics.CreateAPIView):
    model = Interview
    serializer_class = InterviewSerializer
    permission_classes = [permissions.IsAuthenticated]


class OfferCreateView(ApplicationChildMixin, generics.CreateAPIView):
    model = Offer
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]


class ApplicationNoteDetailView(ApplicationChildMixin, generics.RetrieveUpdateDestroyAPIView):
    model = ApplicationNote
    serializer_class = ApplicationNoteSerializer
    permission_classes = [permissions.IsAuthenticated]


class ApplicationReminderDetailView(ApplicationChildMixin, generics.RetrieveUpdateDestroyAPIView):
    model = ApplicationReminder
    serializer_class = ApplicationReminderSerializer
    permission_classes = [permissions.IsAuthenticated]


class InterviewDetailView(ApplicationChildMixin, generics.RetrieveUpdateDestroyAPIView):
    model = Interview
    serializer_class = InterviewSerializer
    permission_classes = [permissions.IsAuthenticated]


class OfferDetailView(ApplicationChildMixin, generics.RetrieveUpdateDestroyAPIView):
    model = Offer
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]
