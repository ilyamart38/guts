# Generated by Django 2.0.2 on 2018-06-05 09:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0056_sw_model_ports_names'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sw_model',
            name='ports_names',
            field=models.CharField(blank=True, max_length=500, verbose_name='Названия портов в конфиге'),
        ),
    ]
