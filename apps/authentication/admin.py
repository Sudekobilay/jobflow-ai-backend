from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
	list_display = ("email", "first_name", "last_name", "is_active", "is_staff", "created_at")
	list_filter = ("is_active", "is_staff", "is_superuser")
	search_fields = ("email", "first_name", "last_name")
	readonly_fields = ("created_at", "updated_at", "last_login", "date_joined")
