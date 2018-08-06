# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-08-04 14:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0012_auto_20180804_2203'),
    ]

    operations = [
        migrations.AlterField(
            model_name='port_type',
            name='connection_type',
            field=models.IntegerField(choices=[(0, 'Магистральный порт'), (1, 'Распределительный порт'), (3, 'PPPoE-подключение'), (4, 'Прочее-подключение'), (5, 'Сигнализатор'), (99, 'Неисправный порт')], default=0, verbose_name='Тип подключения.'),
        ),
    ]