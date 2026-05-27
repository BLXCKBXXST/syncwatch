"""Служебные эндпоинты, не привязанные к доменным приложениям."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import SiteSettings


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    """Проверка живости сервиса (для мониторинга и деплой-скрипта)."""
    return Response({'status': 'ok', 'service': 'syncwatch'})


@api_view(['GET'])
@permission_classes([AllowAny])
def site_settings(request):
    """Глобальные настройки сайта — дефолтная тема для новых пользователей."""
    s = SiteSettings.get_solo()
    return Response({'default_theme': s.default_theme})
