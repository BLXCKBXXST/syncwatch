"""Чистая логика синхронизации воспроизведения в комнате.

Вынесена отдельной функцией без зависимостей от Django, чтобы её было просто
покрыть юнит-тестами — это ядро ключевой функции платформы.
"""


def effective_position(is_playing, playback_position, state_updated_at, now):
    """Текущая позиция воспроизведения с поправкой на прошедшее время.

    Пока комната «играет», позиция растёт вместе с реальным временем; на паузе
    она зафиксирована. state_updated_at и now — объекты datetime.
    """
    if is_playing:
        elapsed = (now - state_updated_at).total_seconds()
        return playback_position + max(0.0, elapsed)
    return playback_position
