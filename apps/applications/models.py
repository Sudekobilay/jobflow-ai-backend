from django.conf import settings
from django.db import models


class CV(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cvs")
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True, default="")
    skills = models.JSONField(default=list, blank=True)
    file = models.FileField(upload_to="cvs/", null=True, blank=True)
    file_type = models.CharField(max_length=20, blank=True, default="")
    parsed_text = models.TextField(blank=True, default="")
    parsed_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.title}"


class CVVersion(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name="versions")
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True, default="")
    skills = models.JSONField(default=list, blank=True)
    parsed_text = models.TextField(blank=True, default="")
    parsed_data = models.JSONField(default=dict, blank=True)
    version_number = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-version_number",)
        constraints = [models.UniqueConstraint(fields=("cv", "version_number"), name="unique_cv_version")]


class CVAnalysis(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cv_analyses")
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name="analyses", null=True, blank=True)
    ats_score = models.PositiveSmallIntegerField()
    strengths = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, default="success")
    error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.email} CV analysis {self.pk}"


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ("saved", "Saved"),
        ("to_apply", "To apply"),
        ("applied", "Applied"),
        ("reviewed", "Reviewed"),
        ("assessment", "Assessment"),
        ("interview", "Interview"),
        ("offer", "Offer"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("withdrawn", "Withdrawn"),
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


class ApplicationStatusHistory(models.Model):
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    from_status = models.CharField(max_length=20, blank=True, default="")
    to_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-changed_at",)


class ApplicationNote(models.Model):
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name="notes")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class ApplicationReminder(models.Model):
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name="reminders")
    remind_at = models.DateTimeField()
    message = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)


class Interview(models.Model):
    application = models.OneToOneField(JobApplication, on_delete=models.CASCADE, related_name="interview")
    scheduled_at = models.DateTimeField()
    interview_type = models.CharField(max_length=20, default="video")
    interviewer = models.CharField(max_length=200, blank=True, default="")
    notes = models.TextField(blank=True, default="")


class Offer(models.Model):
    application = models.OneToOneField(JobApplication, on_delete=models.CASCADE, related_name="offer")
    salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default="USD")
    offered_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")