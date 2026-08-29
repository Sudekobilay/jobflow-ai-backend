from django.conf import settings
from django.db import models


class Job(models.Model):
    SOURCE_CHOICES = [
        ("manual", "Manual"),
        ("remoteok", "RemoteOK"),
        ("arbeitnow", "Arbeitnow"),
        ("adzuna", "Adzuna"),
        ("jooble", "Jooble"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="jobs_created", null=True, blank=True)
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True, default="")
    description = models.TextField()
    salary = models.CharField(max_length=100, blank=True, default="")
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_remote = models.BooleanField(default=False)
    technologies = models.JSONField(default=list, blank=True)
    experience_level = models.CharField(max_length=50, blank=True, default="")
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default="manual")
    external_id = models.CharField(max_length=255, blank=True, null=True)
    source_url = models.URLField(blank=True, default="")
    published_at = models.DateTimeField(null=True, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("source", "external_id"),
                name="unique_job_source_external_id",
            )
        ]

    def __str__(self):
        return f"{self.company} - {self.title}"


class JobSyncRun(models.Model):
    STATUS_CHOICES = [("running", "Running"), ("success", "Success"), ("failed", "Failed")]
    source = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="running")
    fetched_count = models.PositiveIntegerField(default=0)
    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
