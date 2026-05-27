"""Каталог переехал на TMDB-справочник. Старые источники kinogo/zona
удалены — записи в БД, оставшиеся от первой версии, сносим.
"""

from django.db import migrations, models


def cleanup_old_sources(apps, schema_editor):
    SourceConfig = apps.get_model('catalog', 'SourceConfig')
    SourceConfig.objects.exclude(source_id='tmdb').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(cleanup_old_sources, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='sourceconfig',
            name='source_id',
            field=models.CharField(
                choices=[('tmdb', 'TMDB')],
                max_length=16,
                unique=True,
                verbose_name='идентификатор источника',
            ),
        ),
        migrations.AlterField(
            model_name='sourceconfig',
            name='base_url',
            field=models.URLField(
                help_text='Для TMDB: https://api.themoviedb.org/3',
                max_length=255,
                verbose_name='базовый URL API',
            ),
        ),
        migrations.AlterField(
            model_name='sourceconfig',
            name='username',
            field=models.CharField(
                blank=True,
                max_length=120,
                verbose_name='логин (если требуется)',
            ),
        ),
        migrations.AlterField(
            model_name='sourceconfig',
            name='password',
            field=models.CharField(
                blank=True,
                help_text='Для TMDB — v3 API key с https://www.themoviedb.org/settings/api',
                max_length=255,
                verbose_name='API key',
            ),
        ),
    ]
