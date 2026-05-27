"""Модели комнат совместного просмотра."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from common.models import TimeStampedModel, UUIDModel
from videos.models import Video


class WatchRoom(UUIDModel, TimeStampedModel):
    """Комната синхронного просмотра видео.

    Состояние плеера (позиция, пауза) — общее для всех зрителей; авторитетом
    является ведущий (host). UUID комнаты служит токеном ссылки-приглашения.
    """

    # Источник видео — либо загруженное в платформу, либо ссылка на страницу
    # с произвольного сайта (резолвится yt-dlp в прямой поток).
    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name='rooms',
        verbose_name='видео',
        null=True,
        blank=True,
    )
    external_url = models.CharField('страница внешнего видео', max_length=2048, blank=True)
    external_kind = models.CharField('тип внешнего источника', max_length=32, blank=True)
    stream_url = models.CharField('извлечённый прямой поток', max_length=4096, blank=True)
    external_title = models.CharField('название внешнего ролика', max_length=300, blank=True)
    external_duration = models.FloatField('длительность, с', null=True, blank=True)
    external_thumbnail_url = models.URLField('обложка', max_length=2048, blank=True)
    external_resolved_at = models.DateTimeField('поток обновлён', null=True, blank=True)

    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hosted_rooms',
        verbose_name='ведущий',
    )
    title = models.CharField('название комнаты', max_length=200, blank=True)
    is_active = models.BooleanField('активна', default=True)

    # Состояние плеера комнаты.
    playback_position = models.FloatField('позиция, с', default=0.0)
    is_playing = models.BooleanField('воспроизводится', default=False)
    state_updated_at = models.DateTimeField('состояние обновлено', default=timezone.now)

    class Meta:
        verbose_name = 'комната просмотра'
        verbose_name_plural = 'комнаты просмотра'
        ordering = ('-created_at',)

    def __str__(self):
        return self.title or f'Комната {self.pk}'

    @property
    def is_external(self):
        # Комната считается внешней, если у неё есть сохранённый stream_url
        # (загруженное видео отдаётся через video.file, у него stream_url пуст).
        return bool(self.stream_url)

    @property
    def display_title(self):
        if self.title:
            return self.title
        if self.is_external:
            return self.external_title or self.external_url
        return self.video.title if self.video_id else 'Комната'


class RoomParticipant(TimeStampedModel):
    """Участник комнаты — зарегистрированный пользователь или гость."""

    ROLE_HOST = 'host'
    ROLE_VIEWER = 'viewer'
    ROLE_CHOICES = ((ROLE_HOST, 'Ведущий'), (ROLE_VIEWER, 'Зритель'))

    room = models.ForeignKey(
        WatchRoom, on_delete=models.CASCADE, related_name='participants'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='room_participations',
    )
    guest_label = models.CharField('имя гостя', max_length=80, blank=True)
    role = models.CharField('роль', max_length=10, choices=ROLE_CHOICES, default=ROLE_VIEWER)
    is_online = models.BooleanField('онлайн', default=False)
    joined_at = models.DateTimeField('подключился', default=timezone.now)
    left_at = models.DateTimeField('отключился', null=True, blank=True)

    class Meta:
        verbose_name = 'участник комнаты'
        verbose_name_plural = 'участники комнаты'
        constraints = [
            # Один зарегистрированный пользователь — одна запись на комнату.
            models.UniqueConstraint(
                fields=['room', 'user'],
                condition=models.Q(user__isnull=False),
                name='uniq_room_user',
            ),
        ]

    def __str__(self):
        return f'{self.display_name} @ {self.room_id}'

    @property
    def display_name(self):
        if self.user_id:
            return self.user.display_name
        return self.guest_label or 'Гость'
