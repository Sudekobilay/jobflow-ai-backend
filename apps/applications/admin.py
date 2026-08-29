from django.contrib import admin
from .models import (
	ApplicationNote, ApplicationReminder, ApplicationStatusHistory, CV, CVAnalysis,
	CVVersion, Interview, JobApplication, Offer,
)


@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
	list_display = ("title", "user", "file_type", "created_at", "updated_at")
	search_fields = ("title", "user__email", "summary", "parsed_text")
	readonly_fields = ("created_at", "updated_at")


@admin.register(CVVersion)
class CVVersionAdmin(admin.ModelAdmin):
	list_display = ("cv", "version_number", "created_at")
	search_fields = ("cv__title", "cv__user__email")
	readonly_fields = ("created_at",)


@admin.register(CVAnalysis)
class CVAnalysisAdmin(admin.ModelAdmin):
	list_display = ("user", "cv", "ats_score", "status", "created_at")
	list_filter = ("status", "created_at")
	search_fields = ("user__email", "cv__title")
	readonly_fields = ("created_at",)


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
	list_display = ("user", "job", "status", "created_at", "updated_at")
	list_filter = ("status", "created_at")
	search_fields = ("user__email", "job__title", "job__company")
	readonly_fields = ("created_at", "updated_at")


admin.site.register((ApplicationStatusHistory, ApplicationNote, ApplicationReminder, Interview, Offer))
