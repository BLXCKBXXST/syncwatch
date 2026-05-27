"""Регистрация моделей accounts в админке."""

from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'display_name', 'is_guest',
        'is_active', 'is_staff', 'last_seen', 'date_joined',
    )
    search_fields = ('username', 'email', 'first_name', 'last_name', 'chat_display_name')
    list_filter = ('is_guest', 'is_active', 'is_staff')
    ordering = ('-date_joined',)
