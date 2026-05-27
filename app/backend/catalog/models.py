"""Настройки источников каталога.

Одна запись на источник. Меняется через `/admin/` без редеплоя: токен
выдан — открываешь админку и вставляешь в поле API key. Парсер
подхватит изменение в течение 30 секунд.
"""

from django.db import models


class SourceConfig(models.Model):
    """Конфигурация одного источника каталога."""

    SOURCE_KINOPOISKDEV = 'kinopoiskdev'
    SOURCE_CHOICES = (
        (SOURCE_KINOPOISKDEV, 'poiskkino.dev'),
    )

    source_id = models.CharField(
        'идентификатор источника',
        max_length=16,
        choices=SOURCE_CHOICES,
        unique=True,
    )
    base_url = models.URLField(
        'базовый URL API',
        max_length=255,
        help_text='Для poiskkino.dev: https://api.poiskkino.dev',
    )
    username = models.CharField(
        'логин (если требуется)',
        max_length=120,
        blank=True,
    )
    password = models.CharField(
        'API key',
        max_length=255,
        blank=True,
        help_text='Токен от @poiskkinodev_bot в Telegram',
    )
    is_active = models.BooleanField('включён', default=True)
    notes = models.TextField('заметки', blank=True)

    created_at = models.DateTimeField('создано', auto_now_add=True)
    updated_at = models.DateTimeField('изменено', auto_now=True)

    class Meta:
        verbose_name = 'источник каталога'
        verbose_name_plural = 'источники каталога'
        ordering = ('source_id',)

    def __str__(self):
        return f'{self.get_source_id_display()} → {self.base_url}'
