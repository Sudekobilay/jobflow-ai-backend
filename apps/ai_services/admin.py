from django.contrib import admin
from .models import AIUsage, AssistantConversation, AssistantMessage, JobMatch


@admin.register(AIUsage)
class AIUsageAdmin(admin.ModelAdmin):
	list_display = ("user", "endpoint", "model", "total_tokens", "estimated_cost", "outcome", "created_at")
	list_filter = ("outcome", "provider", "model", "created_at")
	search_fields = ("user__email", "endpoint", "fallback_reason", "error_type")
	readonly_fields = ("created_at",)


@admin.register(JobMatch)
class JobMatchAdmin(admin.ModelAdmin):
	list_display = ("user", "job", "cv", "match_score", "status", "created_at")
	list_filter = ("status", "created_at")
	search_fields = ("user__email", "job__title", "job__company")
	readonly_fields = ("created_at",)


@admin.register(AssistantConversation)
class AssistantConversationAdmin(admin.ModelAdmin):
	list_display = ("user", "title", "created_at", "updated_at")
	search_fields = ("user__email", "title")
	readonly_fields = ("created_at", "updated_at")


@admin.register(AssistantMessage)
class AssistantMessageAdmin(admin.ModelAdmin):
	list_display = ("conversation", "role", "created_at")
	list_filter = ("role", "created_at")
	search_fields = ("content", "conversation__user__email")
	readonly_fields = ("created_at",)
