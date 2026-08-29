from django.conf import settings
from django.db import models


class AssistantConversation(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assistant_conversations")
	title = models.CharField(max_length=200, blank=True, default="Career Assistant")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("-updated_at",)


class AssistantMessage(models.Model):
	ROLE_CHOICES = [("user", "User"), ("assistant", "Assistant")]
	conversation = models.ForeignKey(AssistantConversation, on_delete=models.CASCADE, related_name="messages")
	role = models.CharField(max_length=20, choices=ROLE_CHOICES)
	content = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ("created_at",)


class AIUsage(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_usage")
	endpoint = models.CharField(max_length=100)
	provider = models.CharField(max_length=50, blank=True, default="")
	model = models.CharField(max_length=100, blank=True, default="")
	status_code = models.PositiveSmallIntegerField()
	input_chars = models.PositiveIntegerField(default=0)
	output_chars = models.PositiveIntegerField(default=0)
	input_tokens = models.PositiveIntegerField(default=0)
	output_tokens = models.PositiveIntegerField(default=0)
	total_tokens = models.PositiveIntegerField(default=0)
	estimated_cost = models.DecimalField(max_digits=12, decimal_places=8, default=0)
	outcome = models.CharField(max_length=20, default="success")
	fallback_reason = models.CharField(max_length=100, blank=True, default="")
	error_type = models.CharField(max_length=100, blank=True, default="")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ("-created_at",)


class JobMatch(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="job_matches")
	cv = models.ForeignKey("applications.CV", on_delete=models.SET_NULL, null=True, blank=True, related_name="job_matches")
	job = models.ForeignKey("jobs.Job", on_delete=models.CASCADE, related_name="job_matches")
	match_score = models.PositiveSmallIntegerField()
	matching_skills = models.JSONField(default=list, blank=True)
	missing_skills = models.JSONField(default=list, blank=True)
	explanation = models.TextField(blank=True, default="")
	status = models.CharField(max_length=20, default="success")
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ("-created_at",)
