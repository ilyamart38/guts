# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-07-30 09:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0005_auto_20180730_0856'),
    ]

    operations = [
        migrations.RenameField(
            model_name='mgs',
            old_name='campuss',
            new_name='campus_counter',
        ),
        migrations.RenameField(
            model_name='mgs',
            old_name='nodes',
            new_name='node_counter',
        ),
        migrations.RenameField(
            model_name='mgs',
            old_name='switches',
            new_name='switche_counter',
        ),
    ]