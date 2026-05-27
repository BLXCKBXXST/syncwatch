from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'default_theme',
                    models.CharField(
                        choices=[
                            ('default', 'blxck.hub (тёмная)'),
                            ('seans', 'СЕАНС'),
                            ('sonar', 'Sonar'),
                        ],
                        default='default',
                        help_text=(
                            'Тема, которую видят пользователи при первом заходе. '
                            'Если пользователь сам выбрал тему — его выбор сохраняется.'
                        ),
                        max_length=20,
                        verbose_name='тема по умолчанию',
                    ),
                ),
                (
                    'updated_at',
                    models.DateTimeField(auto_now=True, verbose_name='обновлено'),
                ),
            ],
            options={
                'verbose_name': 'настройки сайта',
                'verbose_name_plural': 'настройки сайта',
            },
        ),
    ]
