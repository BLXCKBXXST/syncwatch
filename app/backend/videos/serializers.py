"""Сериализаторы приложения videos."""

from django.conf import settings
from rest_framework import serializers

from .models import Video


class VideoSerializer(serializers.ModelSerializer):
    """Представление видео для ленты и страницы просмотра."""

    owner = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    stream_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = (
            'id', 'title', 'description', 'owner', 'duration_seconds',
            'size_bytes', 'content_type', 'views_count', 'is_public',
            'created_at', 'thumbnail_url', 'stream_url',
        )

    def get_owner(self, obj):
        return {'id': obj.owner_id, 'display_name': obj.owner.display_name}

    def get_thumbnail_url(self, obj):
        return obj.thumbnail.url if obj.thumbnail else None

    def get_stream_url(self, obj):
        return f'/api/videos/{obj.id}/stream/'


class VideoUploadSerializer(serializers.ModelSerializer):
    """Загрузка нового ролика (multipart/form-data).

    Флаг is_public сюда не входит намеренно: BooleanField в multipart трактует
    отсутствующее поле как False. Признак публичности разбирается во вьюхе.
    """

    class Meta:
        model = Video
        fields = ('title', 'description', 'file', 'thumbnail')

    def validate_file(self, value):
        if value.size > settings.MAX_UPLOAD_SIZE:
            limit_mb = settings.MAX_UPLOAD_SIZE // (1024 * 1024)
            raise serializers.ValidationError(
                f'Файл больше допустимого размера ({limit_mb} МБ).'
            )
        return value


class VideoUpdateSerializer(serializers.ModelSerializer):
    """Правка метаданных уже загруженного ролика."""

    class Meta:
        model = Video
        fields = ('title', 'description', 'is_public')
