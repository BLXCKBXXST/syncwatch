"""Удаление гостевых аккаунтов, неактивных дольше заданного срока.

Запускается периодически (фоновым циклом из entrypoint.sh). Аккаунты удаляются
по одному через user.delete(): так для каждого видео срабатывает сигнал
pre_delete, очищающий файлы с диска, а каскад БД сносит комнаты, сообщения
чата, вопросы и ответы гостя.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Удаляет неактивные гостевые аккаунты со всем их контентом.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours', type=int, default=24,
            help='Порог простоя в часах (по умолчанию 24).',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Только показать, сколько аккаунтов было бы удалено.',
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=options['hours'])
        user_model = get_user_model()
        stale = user_model.objects.filter(is_guest=True, last_seen__lt=cutoff)
        count = stale.count()

        if options['dry_run']:
            self.stdout.write(f'Будет удалено гостевых аккаунтов: {count}')
            return

        for user in stale.iterator():
            user.delete()
        self.stdout.write(f'Удалено неактивных гостевых аккаунтов: {count}')
