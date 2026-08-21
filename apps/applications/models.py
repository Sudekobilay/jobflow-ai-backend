from django.conf import settings
from django.db import models


class CV(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cvs")
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True, default="")
    skills = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.title}"


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ("applied", "Applied"),
        ("reviewed", "Reviewed"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_applications",
    )
    job = models.ForeignKey(
        "jobs.Job",
        on_delete=models.CASCADE,
        related_name="applications",
    )
    cv = models.ForeignKey(
        "CV",
        on_delete=models.CASCADE,
        related_name="applications",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="applied",
    )
    cover_letter = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "job")

    def __str__(self):
        return f"{self.user.email} -> {self.job.title}"