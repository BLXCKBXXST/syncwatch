"""Сервисный слой аккаунтов: выпуск JWT-токенов и формирование ответа авторизации.

Вынесено из views, чтобы выдача токенов имела одну точку определения
(SOLID — единая ответственность).
"""

from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserSerializer


def issue_jwt_pair(user):
    """Формирует пару JWT-токенов (access + refresh) для пользователя."""
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


def auth_response(user):
    """Единый ответ авторизации: пара токенов + сериализованный пользователь."""
    return {**issue_jwt_pair(user), 'user': UserSerializer(user).data}
