"""Middleware трекинга активности: обновляет last_seen у вошедших пользователей.

Нужен, чтобы отсчитывать 24-часовой простой гостевых аккаунтов. Запись
троттлится — не чаще одного UPDATE в 5 минут на пользователя, поэтому почти
не нагружает БД.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

THROTTLE = timedelta(minutes=5)


class LastSeenMiddleware:
    """Помечает last_seen текущим временем после обработки запроса."""

    def __init__(self, get_response):
        self.get_response = get_response
        # request.user — это SimpleLazyObject; type(user) даст обёртку,
        # а не настоящий User. Берём класс явно через get_user_model().
        self.user_model = get_user_model()

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            now = timezone.now()
            last = getattr(user, 'last_seen', None)
            if last is None or now - last > THROTTLE:
                # update() — один дешёвый UPDATE, без save()/сигналов.
                self.user_model.objects.filter(pk=user.pk).update(last_seen=now)
        return response
