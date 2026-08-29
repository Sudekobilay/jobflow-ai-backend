from django.contrib import admin
from .models import Job, JobSyncRun


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
	list_display = ("title", "company", "source", "is_active", "published_at", "expires_at")
	list_filter = ("source", "is_active", "is_remote", "experience_level")
	search_fields = ("title", "company", "description", "external_id")
	readonly_fields = ("created_at", "updated_at", "synced_at")


@admin.register(JobSyncRun)
class JobSyncRunAdmin(admin.ModelAdmin):
	list_display = ("source", "status", "fetched_count", "created_count", "updated_count", "started_at", "finished_at")
	list_filter = ("source", "status")
	readonly_fields = ("started_at", "finished_at")
