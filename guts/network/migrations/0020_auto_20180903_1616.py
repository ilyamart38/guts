# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-09-03 08:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0019_auto_20180903_1601'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sw_model',
            old_name='botrom_file',
            new_name='bootrom_file',
        ),
        migrations.AlterField(
            model_name='sw_model',
            name='cfg_template',
            field=models.FileField(blank=True, upload_to='cfg_templates', verbose_name='Шаблон конфигурации'),
        ),
    ]
