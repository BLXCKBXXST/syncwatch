"""Эндпоинты авторизации (username/пароль, гость) и профиля пользователя."""

from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer
from .services import auth_response


class RegisterView(APIView):
    """Регистрация по username/паролю — сразу авторизует (выдаёт пару токенов)."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(auth_response(user), status=201)


class LoginView(APIView):
    """Вход по имени пользователя и паролю."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(auth_response(serializer.validated_data['user']))


class GuestView(APIView):
    """Создаёт гостевой аккаунт и сразу его авторизует."""

    permission_classes = [AllowAny]

    def post(self, request):
        user = User.objects.create_guest()
        return Response(auth_response(user), status=201)


class MeView(RetrieveUpdateAPIView):
    """Текущий пользователь: чтение профиля и правка (в т.ч. имени в чате)."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
