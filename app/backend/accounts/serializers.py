"""Сериализаторы приложения accounts."""

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Публичное представление пользователя (профиль, ответ авторизации)."""

    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'chat_display_name', 'display_name', 'is_guest',
        )
        read_only_fields = ('id', 'username', 'display_name', 'is_guest')


class RegisterSerializer(serializers.Serializer):
    """Регистрация по имени пользователя и паролю."""

    username = serializers.CharField(
        min_length=3, max_length=150, validators=[ASCIIUsernameValidator()]
    )
    password = serializers.CharField(write_only=True)
    chat_display_name = serializers.CharField(
        max_length=150, required=False, allow_blank=True
    )

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Это имя пользователя уже занято.')
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Вход по имени пользователя и паролю."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    default_error_messages = {
        'invalid': 'Неверное имя пользователя или пароль.',
    }

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if user is None or not user.is_active:
            self.fail('invalid')
        attrs['user'] = user
        return attrs
