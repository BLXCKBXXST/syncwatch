"""Базовые абстрактные модели — точка повторного использования (DRY)."""

import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """Добавляет отметки создания и изменения записи."""

    created_at = models.DateTimeField('создано', auto_now_add=True)
    updated_at = models.DateTimeField('изменено', auto_now=True)

    class Meta:
        abstract = True
        ordering = ('-created_at',)


class UUIDModel(models.Model):
    """Первичный ключ — UUID (непредсказуемые ссылки на видео и комнаты)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class SiteSettings(models.Model):
    """Глобальные настройки сайта. Singleton: всегда одна запись с pk=1."""

    THEME_CHOICES = [
        ('default', 'blxck.hub (тёмная)'),
        ('seans', 'СЕАНС'),
        ('sonar', 'Sonar'),
    ]

    default_theme = models.CharField(
        'тема по умолчанию',
        max_length=20,
        choices=THEME_CHOICES,
        default='default',
        help_text='Тема, которую видят пользователи при первом заходе. '
                  'Если пользователь сам выбрал тему — его выбор сохраняется.',
    )
    updated_at = models.DateTimeField('обновлено', auto_now=True)

    class Meta:
        verbose_name = 'настройки сайта'
        verbose_name_plural = 'настройки сайта'

    def __str__(self):
        return f'Настройки сайта (тема: {self.get_default_theme_display()})'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
