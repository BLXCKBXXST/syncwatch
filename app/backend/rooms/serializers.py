"""Сериализаторы приложения rooms."""

from django.utils import timezone
from rest_framework import serializers

from videos.serializers import VideoSerializer

from .external_video import resolve_external
from .models import WatchRoom
from .sync import effective_position


class WatchRoomSerializer(serializers.ModelSerializer):
    """Полное представление комнаты с вложенным видео и текущим состоянием."""

    video = VideoSerializer(read_only=True)
    host = serializers.SerializerMethodField()
    is_host = serializers.SerializerMethodField()
    playback_position = serializers.SerializerMethodField()
    participants_count = serializers.SerializerMethodField()
    is_external = serializers.SerializerMethodField()
    stream_url = serializers.SerializerMethodField()
    display_title = serializers.SerializerMethodField()

    class Meta:
        model = WatchRoom
        fields = (
            'id', 'title', 'display_title', 'video', 'host', 'is_host', 'is_active',
            'is_playing', 'playback_position', 'participants_count', 'created_at',
            'is_external', 'external_url', 'external_title',
            'external_thumbnail_url', 'external_duration', 'stream_url',
        )

    def get_host(self, obj):
        return {'id': obj.host_id, 'display_name': obj.host.display_name}

    def get_is_host(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and user.id == obj.host_id

    def get_playback_position(self, obj):
        position = effective_position(
            obj.is_playing, obj.playback_position, obj.state_updated_at, timezone.now()
        )
        return round(position, 3)

    def get_participants_count(self, obj):
        return obj.participants.filter(is_online=True).count()

    def get_is_external(self, obj):
        return obj.is_external

    def get_display_title(self, obj):
        return obj.display_title

    def get_stream_url(self, obj):
        # У внешнего источника прямой URL уже сохранён в комнате; у загруженного
        # видео отдаём наш HTTP-эндпоинт стриминга.
        if obj.is_external:
            return obj.stream_url
        if obj.video_id:
            return f'/api/videos/{obj.video_id}/stream/'
        return ''


class RoomCreateSerializer(serializers.ModelSerializer):
    """Создание комнаты под загруженное видео или внешний URL."""

    external_url = serializers.CharField(required=False, allow_blank=True, max_length=2048)

    class Meta:
        model = WatchRoom
        fields = ('id', 'video', 'external_url', 'title')
        read_only_fields = ('id',)
        extra_kwargs = {'video': {'required': False, 'allow_null': True}}

    def validate(self, attrs):
        video = attrs.get('video')
        external_url = (attrs.get('external_url') or '').strip()
        if not video and not external_url:
            raise serializers.ValidationError(
                'Нужно указать либо загруженное видео (video), либо внешний URL (external_url).'
            )
        if video and external_url:
            raise serializers.ValidationError(
                'Нельзя одновременно задавать загруженное видео и внешний URL.'
            )
        attrs['external_url'] = external_url
        return attrs

    def create(self, validated_data):
        external_url = validated_data.pop('external_url', '')
        if external_url:
            info = resolve_external(external_url)
            validated_data.update({
                'external_url': external_url,
                'external_kind': info['kind'],
                'stream_url': info['url'],
                'external_title': info['title'],
                'external_duration': info['duration'],
                'external_thumbnail_url': info['thumbnail'],
                'external_resolved_at': timezone.now(),
            })
        return super().create(validated_data)
