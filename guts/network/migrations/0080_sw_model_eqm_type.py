# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-07-25 05:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0079_auto_20180719_1226'),
    ]

    operations = [
        migrations.AddField(
            model_name='sw_model',
            name='eqm_type',
            field=models.CharField(default='', max_length=100, verbose_name='Тип объекта в eqm'),
        ),
    ]