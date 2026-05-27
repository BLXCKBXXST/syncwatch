"""Модель видеоролика."""

from django.conf import settings
from django.db import models

from common.models import TimeStampedModel, UUIDModel


def video_upload_path(instance, filename):
    """Каждый ролик хранится в собственной папке по UUID."""
    return f'videos/{instance.id}/{filename}'


def thumbnail_upload_path(instance, filename):
    return f'thumbnails/{instance.id}/{filename}'


class Video(UUIDModel, TimeStampedModel):
    """Загруженное видео и его метаданные."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='videos',
        verbose_name='автор',
    )
    title = models.CharField('название', max_length=200)
    description = models.TextField('описание', blank=True)
    file = models.FileField('файл', upload_to=video_upload_path)
    thumbnail = models.ImageField(
        'превью', upload_to=thumbnail_upload_path, null=True, blank=True
    )
    duration_seconds = models.PositiveIntegerField('длительность, с', default=0)
    size_bytes = models.PositiveBigIntegerField('размер, байт', default=0)
    content_type = models.CharField('MIME-тип', max_length=100, default='video/mp4')
    views_count = models.PositiveIntegerField('просмотры', default=0)
    is_public = models.BooleanField('опубликовано', default=True)

    class Meta:
        verbose_name = 'видео'
        verbose_name_plural = 'видео'
        ordering = ('-created_at',)

    def __str__(self):
        return self.title
