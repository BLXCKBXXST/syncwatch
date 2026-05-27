"""Каталог переехал с TMDB на kinopoisk.dev (TMDB заблокирован)."""

from django.db import migrations, models


def cleanup_old_sources(apps, schema_editor):
    SourceConfig = apps.get_model('catalog', 'SourceConfig')
    SourceConfig.objects.exclude(source_id='kinopoiskdev').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_tmdb_source'),
    ]

    operations = [
        migrations.RunPython(cleanup_old_sources, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='sourceconfig',
            name='source_id',
            field=models.CharField(
                choices=[('kinopoiskdev', 'Кинопоиск')],
                max_length=16,
                unique=True,
                verbose_name='идентификатор источника',
            ),
        ),
        migrations.AlterField(
            model_name='sourceconfig',
            name='base_url',
            field=models.URLField(
                help_text='Для Кинопоиска: https://api.kinopoisk.dev',
                max_length=255,
                verbose_name='базовый URL API',
            ),
        ),
        migrations.AlterField(
            model_name='sourceconfig',
            name='password',
            field=models.CharField(
                blank=True,
                help_text='Для Кинопоиска — токен от @kinopoiskdev_bot в Telegram',
                max_length=255,
                verbose_name='API key',
            ),
        ),
    ]
