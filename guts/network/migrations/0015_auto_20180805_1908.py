# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-08-05 11:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0014_access_switch_stp_root'),
    ]

    operations = [
        migrations.AlterField(
            model_name='port_of_access_switch',
            name='t_vlans',
            field=models.CharField(blank=True, max_length=1000),
        ),
    ]