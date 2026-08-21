from django.conf import settings
from django.db import models


class Job(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="jobs_created", null=True, blank=True)
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True, default="")
    description = models.TextField()
    salary = models.CharField(max_length=100, blank=True, default="")
    is_remote = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company} - {self.title}"
