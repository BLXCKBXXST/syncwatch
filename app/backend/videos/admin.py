"""Регистрация модели Video в админке."""

from django.contrib import admin

from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'duration_seconds', 'views_count', 'is_public', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('title', 'description', 'owner__email')
    readonly_fields = ('id', 'size_bytes', 'content_type', 'duration_seconds', 'views_count')
