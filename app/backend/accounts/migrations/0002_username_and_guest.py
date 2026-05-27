"""Переход с входа по e-mail на вход по username + добавление гостевых полей.

Порядок операций важен: сначала username добавляется как nullable, затем
заполняется для существующих строк, и только потом на него вешается UNIQUE.
"""

import re

import django.contrib.auth.validators
import django.utils.timezone
from django.db import migrations, models


def backfill_usernames(apps, schema_editor):
    """Заполняет username для существующих пользователей из local-part e-mail."""
    User = apps.get_model('accounts', 'User')
    taken = set()
    for user in User.objects.all().order_by('pk'):
        if user.username:
            taken.add(user.username.lower())
            continue
        base = re.sub(r'[^A-Za-z0-9_.+-]', '', (user.email or '').split('@')[0])
        base = (base or f'user_{user.pk}')[:140]
        candidate = base
        if candidate.lower() in taken:
            candidate = f'{base}_{user.pk}'
        user.username = candidate[:150]
        taken.add(user.username.lower())
        user.save(update_fields=['username'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=150, null=True, verbose_name='имя пользователя'),
        ),
        migrations.AddField(
            model_name='user',
            name='is_guest',
            field=models.BooleanField(db_index=True, default=False, verbose_name='гостевой аккаунт'),
        ),
        migrations.AddField(
            model_name='user',
            name='last_seen',
            field=models.DateTimeField(
                db_index=True,
                default=django.utils.timezone.now,
                verbose_name='последняя активность',
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, default='', max_length=254, verbose_name='e-mail'),
        ),
        migrations.RunPython(backfill_usernames, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(
                max_length=150,
                unique=True,
                validators=[django.contrib.auth.validators.ASCIIUsernameValidator()],
                verbose_name='имя пользователя',
            ),
        ),
    ]
