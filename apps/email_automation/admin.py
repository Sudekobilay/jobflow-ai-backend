from django.contrib import admin
from .models import EmailDelivery, EmailDraft, GmailAccount, GmailOAuthState


@admin.register(EmailDraft)
class EmailDraftAdmin(admin.ModelAdmin):
	list_display = ("user", "recipient_email", "subject", "status", "created_at", "sent_at")
	list_filter = ("status", "created_at")
	search_fields = ("user__email", "recipient_email", "subject")
	readonly_fields = ("approved_at", "sent_at", "created_at", "updated_at")


@admin.register(EmailDelivery)
class EmailDeliveryAdmin(admin.ModelAdmin):
	list_display = ("draft", "status", "attempt_count", "delivered_at")
	list_filter = ("status", "delivered_at")
	readonly_fields = ("delivered_at",)


@admin.register(GmailAccount)
class GmailAccountAdmin(admin.ModelAdmin):
	list_display = ("user", "email", "created_at", "updated_at")
	search_fields = ("user__email", "email")
	readonly_fields = ("encrypted_refresh_token", "created_at", "updated_at")


@admin.register(GmailOAuthState)
class GmailOAuthStateAdmin(admin.ModelAdmin):
	list_display = ("user", "created_at")
	readonly_fields = ("state", "created_at")
