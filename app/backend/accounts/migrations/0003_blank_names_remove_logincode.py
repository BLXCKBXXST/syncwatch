"""Имя/фамилия становятся необязательными; модель одноразовых кодов удаляется."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_username_and_guest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='first_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='имя'),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='фамилия'),
        ),
        migrations.DeleteModel(
            name='LoginCode',
        ),
    ]
