"""Модели аккаунтов: вход по username/паролю плюс гостевые аккаунты."""

import secrets

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Менеджер пользователей: обычные аккаунты с паролем и гостевые без пароля."""

    use_in_migrations = True

    def create_user(self, username, password=None, email='', **extra):
        if not username:
            raise ValueError('Имя пользователя обязательно')
        email = self.normalize_email(email) if email else ''
        user = self.model(username=username, email=email, **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()  # гости и суперпользователь без пароля
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, email='', **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        if not password:
            raise ValueError('Суперпользователю нужен пароль')
        return self.create_user(username, password=password, email=email, **extra)

    def create_guest(self):
        """Создаёт гостевой аккаунт со случайным именем и без пароля."""
        for _ in range(10):
            username = f'guest_{secrets.token_hex(4)}'
            if not self.filter(username=username).exists():
                break
        else:
            raise RuntimeError('Не удалось подобрать уникальное имя для гостя')
        label = f'Гость-{secrets.randbelow(10000):04d}'
        return self.create_user(username=username, is_guest=True, chat_display_name=label)


class User(AbstractBaseUser, PermissionsMixin):
    """Пользователь платформы. Вход по имени пользователя и паролю."""

    username = models.CharField(
        'имя пользователя',
        max_length=150,
        unique=True,
        validators=[ASCIIUsernameValidator()],
    )
    # E-mail необязателен и для входа не используется — оставлен для админки.
    email = models.EmailField('e-mail', blank=True, default='')
    first_name = models.CharField('имя', max_length=150, blank=True)
    last_name = models.CharField('фамилия', max_length=150, blank=True)
    # «Имя в чате» из дизайна — отдельное редактируемое имя для комнат.
    chat_display_name = models.CharField('имя в чате', max_length=150, blank=True)
    is_guest = models.BooleanField('гостевой аккаунт', default=False, db_index=True)
    is_active = models.BooleanField('активен', default=True)
    is_staff = models.BooleanField('доступ в админку', default=False)
    date_joined = models.DateTimeField('дата регистрации', default=timezone.now)
    # Обновляется при активности; по нему чистятся неактивные гостевые аккаунты.
    last_seen = models.DateTimeField('последняя активность', default=timezone.now, db_index=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'
        ordering = ('-date_joined',)

    def __str__(self):
        return self.username

    @property
    def display_name(self):
        """Имя для показа в чате: явное «имя в чате» или имя по умолчанию."""
        return self.chat_display_name or self.first_name or self.username
