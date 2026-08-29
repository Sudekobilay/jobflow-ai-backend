from django.contrib import admin
from .models import Certificate, Language, Skill, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
	list_display = ("user", "university", "department", "gpa", "experience_years", "updated_at")
	search_fields = ("user__email", "university", "department")
	list_filter = ("university", "department")
	readonly_fields = ("created_at", "updated_at")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
	search_fields = ("name",)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
	list_display = ("name", "issuer")
	search_fields = ("name", "issuer")


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
	search_fields = ("name",)
