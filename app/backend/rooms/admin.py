"""Регистрация моделей rooms в админке."""

from django.contrib import admin

from .models import RoomParticipant, WatchRoom


@admin.register(WatchRoom)
class WatchRoomAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'video', 'host', 'is_active', 'is_playing', 'created_at')
    list_filter = ('is_active', 'is_playing')
    search_fields = ('title', 'host__email')
    readonly_fields = ('id', 'playback_position', 'state_updated_at')


@admin.register(RoomParticipant)
class RoomParticipantAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'room', 'role', 'is_online', 'joined_at')
    list_filter = ('role', 'is_online')
