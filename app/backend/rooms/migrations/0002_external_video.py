"""Расширение комнат поддержкой внешнего видео (yt-dlp)."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0001_initial'),
        ('rooms', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='watchroom',
            name='video',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='rooms',
                to='videos.video',
                verbose_name='видео',
            ),
        ),
        migrations.AddField(
            model_name='watchroom',
            name='external_url',
            field=models.CharField(blank=True, max_length=2048, verbose_name='страница внешнего видео'),
        ),
        migrations.AddField(
            model_name='watchroom',
            name='external_kind',
            field=models.CharField(blank=True, max_length=32, verbose_name='тип внешнего источника'),
        ),
        migrations.AddField(
            model_name='watchroom',
            name='stream_url',
            field=models.CharField(blank=True, max_length=4096, verbose_name='извлечённый прямой поток'),
        ),
        migrations.AddField(
            model_name='watchroom',
            name='external_title',
            field=models.CharField(blank=True, max_length=300, verbose_name='название внешнего ролика'),
        ),
        migrations.AddField(
            model_name='watchroom',
            name='external_duration',
            field=models.FloatField(blank=True, null=True, verbose_name='длительность, с'),
        ),
        migrations.AddField(
            model_name='watchroom',
            name='external_thumbnail_url',
            field=models.URLField(blank=True, max_length=2048, verbose_name='обложка'),
        ),
        migrations.AddField(
            model_name='watchroom',
            name='external_resolved_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='поток обновлён'),
        ),
    ]
