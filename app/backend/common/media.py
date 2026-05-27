"""Утилиты работы с медиафайлами."""

import json
import subprocess


def probe_duration(path):
    """Возвращает длительность видео в секундах через ffprobe.

    Если ffprobe недоступен (например, в локальной разработке без ffmpeg)
    или файл не распознан — возвращает 0, не прерывая загрузку.
    """
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', path],
            capture_output=True,
            text=True,
            timeout=20,
        )
        data = json.loads(result.stdout)
        return int(float(data['format']['duration']))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        return 0
