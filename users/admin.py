from __future__ import annotations

from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "email", "is_staff", "is_active"]
    list_display_links = ["id", "email"]
    search_fields = ["email", "name"]
