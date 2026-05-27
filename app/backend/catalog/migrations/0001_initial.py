"""Источники каталога — управляются через /admin/."""

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='SourceConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('source_id', models.CharField(
                    choices=[('kinogo', 'Kinogo'), ('zona', 'Zona')],
                    max_length=16,
                    unique=True,
                    verbose_name='идентификатор источника',
                )),
                ('base_url', models.URLField(
                    help_text='Например, https://kinogo.la или личное зеркало от @kinogobiz_bot.',
                    max_length=255,
                    verbose_name='базовый URL зеркала',
                )),
                ('username', models.CharField(
                    blank=True,
                    help_text='Если задан, парсер войдёт под этой учёткой — это убирает рекламу в плеере.',
                    max_length=120,
                    verbose_name='логин (для входа на источнике)',
                )),
                ('password', models.CharField(blank=True, max_length=255, verbose_name='пароль')),
                ('is_active', models.BooleanField(default=True, verbose_name='включён')),
                ('notes', models.TextField(blank=True, verbose_name='заметки')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='создано')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='изменено')),
            ],
            options={
                'verbose_name': 'источник каталога',
                'verbose_name_plural': 'источники каталога',
                'ordering': ('source_id',),
            },
        ),
    ]
