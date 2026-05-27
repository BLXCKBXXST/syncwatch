"""Эндпоинты комнат совместного просмотра.

Живое управление плеером и чат идут по WebSocket (rooms.consumers); REST здесь
отвечает за создание комнаты, чтение её состояния, передачу роли ведущего
и обновление потока внешнего видео.
"""

from django.db import transaction
from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .external_video import resolve_external
from .host_transfer import transfer_host
from .models import RoomParticipant, WatchRoom
from .serializers import RoomCreateSerializer, WatchRoomSerializer


class WatchRoomViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Создание комнаты, чтение по ссылке, список своих и сервисные actions."""

    def get_permissions(self):
        # Открыть комнату по ссылке может любой (в т.ч. гость); создавать,
        # править и просматривать список своих комнат — только авторизованные.
        if self.action == 'retrieve':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        return RoomCreateSerializer if self.action == 'create' else WatchRoomSerializer

    def get_queryset(self):
        qs = WatchRoom.objects.select_related('video', 'video__owner', 'host')
        if self.action == 'list':
            return qs.filter(host=self.request.user)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = RoomCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        room = serializer.save(host=request.user)
        data = WatchRoomSerializer(room, context=self.get_serializer_context()).data
        return Response(data, status=201)

    @action(detail=True, methods=['post'], url_path='refresh-stream')
    def refresh_stream(self, request, pk=None):
        """Повторно резолвит external_url (если signed-URL истёк)."""
        room = self.get_object()
        if room.host_id != request.user.id:
            raise PermissionDenied('Только ведущий может обновить поток.')
        if not room.is_external:
            raise ValidationError('Эта комната не использует внешний источник.')
        info = resolve_external(room.external_url)
        room.stream_url = info['url']
        room.external_kind = info['kind']
        if info['title']:
            room.external_title = info['title']
        if info['duration']:
            room.external_duration = info['duration']
        if info['thumbnail']:
            room.external_thumbnail_url = info['thumbnail']
        room.external_resolved_at = timezone.now()
        room.save(update_fields=[
            'stream_url', 'external_kind', 'external_title',
            'external_duration', 'external_thumbnail_url',
            'external_resolved_at', 'updated_at',
        ])
        return Response(WatchRoomSerializer(room, context=self.get_serializer_context()).data)

    @action(detail=True, methods=['post'], url_path='transfer-host')
    def transfer_host_action(self, request, pk=None):
        """HTTP-fallback к WS-команде передачи ведущего."""
        room = self.get_object()
        if room.host_id != request.user.id:
            raise PermissionDenied('Только текущий ведущий может передать роль.')
        participant_id = request.data.get('participant_id')
        if not participant_id:
            raise ValidationError({'participant_id': 'Обязательное поле.'})
        with transaction.atomic():
            try:
                target = RoomParticipant.objects.select_related('user').get(
                    pk=participant_id, room=room, is_online=True
                )
            except RoomParticipant.DoesNotExist as exc:
                raise ValidationError({'participant_id': 'Участник не найден.'}) from exc
            if not target.user_id:
                raise ValidationError({'participant_id': 'Гостю нельзя передать роль.'})
            if target.user_id == room.host_id:
                raise ValidationError({'participant_id': 'Уже ведущий.'})
            transfer_host(room, target)
        return Response(WatchRoomSerializer(room, context=self.get_serializer_context()).data)
