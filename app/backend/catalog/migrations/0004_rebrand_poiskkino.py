"""Ребрендинг: kinopoisk.dev → poiskkino.dev, новый бот @poiskkinodev_bot."""

from django.db import migrations, models


def update_base_url(apps, schema_editor):
    """Подменяем старый base_url на новый домен (редирект 301 работает,
    но лишний прыжок ни к чему)."""
    SourceConfig = apps.get_model('catalog', 'SourceConfig')
    SourceConfig.objects.filter(
        source_id='kinopoiskdev', base_url__contains='kinopoisk.dev'
    ).update(base_url='https://api.poiskkino.dev')


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0003_kinopoiskdev_source'),
    ]

    operations = [
        migrations.RunPython(update_base_url, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='sourceconfig',
            name='source_id',
            field=models.CharField(
                choices=[('kinopoiskdev', 'poiskkino.dev')],
                max_length=16,
                unique=True,
                verbose_name='идентификатор источника',
            ),
        ),
        migrations.AlterField(
            model_name='sourceconfig',
            name='base_url',
            field=models.URLField(
                help_text='Для poiskkino.dev: https://api.poiskkino.dev',
                max_length=255,
                verbose_name='базовый URL API',
            ),
        ),
        migrations.AlterField(
            model_name='sourceconfig',
            name='password',
            field=models.CharField(
                blank=True,
                help_text='Токен от @poiskkinodev_bot в Telegram',
                max_length=255,
                verbose_name='API key',
            ),
        ),
    ]
