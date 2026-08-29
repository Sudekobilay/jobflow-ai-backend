from django.conf import settings
from django.db import models


class NotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preferences")
    email_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    job_alerts_enabled = models.BooleanField(default=True)
    interview_reminders_enabled = models.BooleanField(default=True)


class Notification(models.Model):
    TYPE_CHOICES = [
        ("job_alert", "Job alert"),
        ("interview", "Interview"),
        ("application", "Application"),
        ("system", "System"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=30, choices=TYPE_CHOICES, default="system")
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_application = models.ForeignKey("applications.JobApplication", on_delete=models.SET_NULL, null=True, blank=True)
    related_job = models.ForeignKey("jobs.Job", on_delete=models.SET_NULL, null=True, blank=True)
    dedupe_key = models.CharField(max_length=150, unique=True, null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
