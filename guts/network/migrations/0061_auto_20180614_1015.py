# Generated by Django 2.0.2 on 2018-06-14 10:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0060_auto_20180607_1511'),
    ]

    operations = [
        migrations.AlterField(
            model_name='port_of_access_switch',
            name='port_name',
            field=models.CharField(max_length=100),
        ),
    ]