# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-07-31 14:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0008_auto_20180731_2146'),
    ]

    operations = [
        migrations.AlterField(
            model_name='access_switch',
            name='cfg_file',
            field=models.FileField(upload_to='cfg_switches'),
        ),
    ]
