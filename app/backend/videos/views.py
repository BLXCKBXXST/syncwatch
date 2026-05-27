"""Эндпоинты загрузки, просмотра и стриминга видео."""

from django.db.models import F
from django.http import Http404
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from common.media import probe_duration
from common.permissions import IsOwnerOrReadOnly
from common.streaming import range_file_response

from .models import Video
from .serializers import VideoSerializer, VideoUpdateSerializer, VideoUploadSerializer


class VideoViewSet(ModelViewSet):
    """CRUD над видео + лента «mine» и стриминг файла с поддержкой Range."""

    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    # Загрузка файла — multipart; правка метаданных — JSON.
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Video.objects.select_related('owner')
        if self.action == 'list':
            return qs.filter(is_public=True)
        if self.action == 'mine':
            if self.request.user.is_authenticated:
                return qs.filter(owner=self.request.user)
            return qs.none()
        return qs

    def get_serializer_class(self):
        if self.action in ('update', 'partial_update'):
            return VideoUpdateSerializer
        return VideoSerializer

    def _ensure_visible(self, video):
        """Закрытое видео доступно только владельцу."""
        if not video.is_public and video.owner_id != getattr(self.request.user, 'id', None):
            raise Http404

    def create(self, request, *args, **kwargs):
        serializer = VideoUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload = serializer.validated_data['file']
        # Публичность приходит строкой; отсутствие значения трактуем как «да».
        is_public = str(request.data.get('is_public', 'true')).lower() not in (
            'false', '0', 'no',
        )
        video = serializer.save(
            owner=request.user,
            size_bytes=getattr(upload, 'size', 0),
            content_type=getattr(upload, 'content_type', '') or 'video/mp4',
            is_public=is_public,
        )
        # Длительность определяется через ffprobe уже по файлу на диске.
        duration = probe_duration(video.file.path)
        if duration:
            video.duration_seconds = duration
            video.save(update_fields=['duration_seconds'])
        data = VideoSerializer(video, context=self.get_serializer_context()).data
        return Response(data, status=201)

    def retrieve(self, request, *args, **kwargs):
        video = self.get_object()
        self._ensure_visible(video)
        # Атомарный инкремент счётчика просмотров.
        Video.objects.filter(pk=video.pk).update(views_count=F('views_count') + 1)
        video.views_count += 1
        data = VideoSerializer(video, context=self.get_serializer_context()).data
        return Response(data)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def mine(self, request):
        """Видео текущего пользователя — для страницы профиля."""
        page = self.paginate_queryset(self.get_queryset())
        serializer = VideoSerializer(page, many=True, context=self.get_serializer_context())
        return self.get_paginated_response(serializer.data)

    @action(detail=True)
    def stream(self, request, pk=None):
        """Отдаёт файл видео с поддержкой запросов Range (перемотка)."""
        video = self.get_object()
        self._ensure_visible(video)
        return range_file_response(
            request, video.file.path, video.content_type or 'video/mp4'
        )
