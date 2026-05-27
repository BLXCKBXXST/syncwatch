"""Регистрация моделей chat в админке."""

from django.contrib import admin

from .models import Answer, ChatMessage, MessageLike, Question, QuestionUpvote


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'room', 'text', 'likes_count', 'created_at')
    search_fields = ('text', 'display_name')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'room', 'text', 'is_answered', 'upvotes_count')
    list_filter = ('is_answered',)


admin.site.register(Answer)
admin.site.register(MessageLike)
admin.site.register(QuestionUpvote)
