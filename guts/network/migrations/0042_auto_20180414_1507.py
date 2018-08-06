# Generated by Django 2.0.2 on 2018-04-14 15:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0041_auto_20180414_1426'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='port_type',
            options={'ordering': ['id'], 'verbose_name': 'Тип порта', 'verbose_name_plural': 'Типы портов'},
        ),
        migrations.AlterModelOptions(
            name='sw_model',
            options={'ordering': ['vendor', 'title'], 'verbose_name': 'Модель коммутаторов', 'verbose_name_plural': 'Модели коммутаторов'},
        ),
        migrations.AddField(
            model_name='access_switch',
            name='ports_descriptions',
            field=models.CharField(blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name='access_switch',
            name='ports_types',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]