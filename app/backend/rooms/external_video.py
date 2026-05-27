"""Извлечение прямой ссылки на видеопоток с произвольной веб-страницы.

Используется yt-dlp: библиотека покрывает тысячи сайтов (YouTube, VK, RuTube,
Twitch, Dailymotion, новостные порталы и т.д.). Никакой загрузки файла,
только парсинг страницы и получение URL потока (mp4 / m3u8).
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from rest_framework import serializers as drf_serializers

logger = logging.getLogger(__name__)


# Опции yt-dlp: тихий режим, без скачивания, предпочитаем mp4 одним файлом
# (без отдельных потоков аудио/видео — иначе плеер не сможет их склеить).
YDL_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'format': 'best[ext=mp4][protocol^=http]/best[ext=mp4]/best',
    'socket_timeout': 15,
    'retries': 1,
}


def resolve_external(url: str) -> dict:
    """Резолвит страницу в прямой видеопоток.

    Возвращает словарь:
        {
            'url': '<прямой mp4/m3u8>',
            'kind': '<extractor key, e.g. youtube/vk>',
            'title': '<заголовок ролика>',
            'duration': <секунды или None>,
            'thumbnail': '<обложка или ''>',
        }

    Бросает rest_framework.exceptions.ValidationError при невалидном URL
    или невозможности извлечь поток.
    """
    if not url or not isinstance(url, str):
        raise drf_serializers.ValidationError({'external_url': 'URL не задан'})

    parsed = urlparse(url.strip())
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        raise drf_serializers.ValidationError(
            {'external_url': 'Ожидается http(s)://… URL страницы с видео'}
        )

    host = parsed.netloc.lower()
    if 'youtube.com' in host or 'youtu.be' in host:
        raise drf_serializers.ValidationError(
            {'external_url':
             'YouTube не поддерживается. Используйте RuTube, VK Video, '
             'Twitch или прямую ссылку на mp4/m3u8.'}
        )

    # yt-dlp импортируем лениво — при первом обращении к комнатам с внешним
    # видео; в тестах подменяется моком, чтобы не лезть в сеть.
    import yt_dlp

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(parsed.geturl(), download=False)
    except yt_dlp.utils.DownloadError as exc:
        logger.warning('yt-dlp не справился с %s: %s', url, exc)
        raise drf_serializers.ValidationError(
            {'external_url': 'Не удалось извлечь видеопоток со страницы'}
        ) from exc
    except Exception as exc:
        logger.exception('Неожиданная ошибка yt-dlp на %s', url)
        raise drf_serializers.ValidationError(
            {'external_url': 'Ошибка при анализе страницы'}
        ) from exc

    if info is None:
        raise drf_serializers.ValidationError(
            {'external_url': 'Страница не содержит видео'}
        )

    # Иногда extract_info возвращает плейлист — берём первый элемент.
    if info.get('_type') == 'playlist' and info.get('entries'):
        info = info['entries'][0]

    stream_url = info.get('url')
    if not stream_url:
        raise drf_serializers.ValidationError(
            {'external_url': 'Не удалось получить прямой URL потока'}
        )

    return {
        'url': stream_url,
        'kind': info.get('extractor_key') or info.get('extractor') or 'generic',
        'title': info.get('title') or '',
        'duration': info.get('duration'),
        'thumbnail': info.get('thumbnail') or '',
    }
