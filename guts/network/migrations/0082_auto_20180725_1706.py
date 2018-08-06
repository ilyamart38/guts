# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-07-25 17:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0081_auto_20180725_1627'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sw_model',
            name='ports_types',
            field=models.CharField(blank=True, help_text='0-Магистральный порт, 1-Распределительный порт, 3-PPPoE-подключение, 4-Прочее-подключение, 5-Сигнализатор, 99-Неисправный порт', max_length=200, verbose_name='Типы портов по умолчанию'),
        ),
    ]