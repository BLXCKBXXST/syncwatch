"""Сигналы приложения videos: очистка файлов с диска при удалении видео."""

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import Video


@receiver(pre_delete, sender=Video)
def delete_video_files(sender, instance, **kwargs):
    """Удаляет файл видео и превью из хранилища, чтобы они не оставались сиротами.

    Срабатывает при любом удалении видео — в т.ч. при каскадном удалении вместе
    с гостевым аккаунтом.
    """
    for field_name in ('file', 'thumbnail'):
        file_field = getattr(instance, field_name, None)
        if file_field:
            file_field.delete(save=False)
