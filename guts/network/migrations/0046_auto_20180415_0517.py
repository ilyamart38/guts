# Generated by Django 2.0.2 on 2018-04-15 05:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0045_auto_20180415_0422'),
    ]

    operations = [
        migrations.AddField(
            model_name='port_type',
            name='is_signal',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='port_type',
            name='non_pppoe',
            field=models.BooleanField(default=False),
        ),
    ]