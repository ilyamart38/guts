# Generated by Django 2.0.2 on 2018-04-14 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0043_auto_20180414_1628'),
    ]

    operations = [
        migrations.AlterField(
            model_name='port_type',
            name='title',
            field=models.CharField(blank=True, max_length=200, verbose_name='Описание типа порта'),
        ),
    ]
