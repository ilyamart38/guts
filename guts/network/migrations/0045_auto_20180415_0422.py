# Generated by Django 2.0.2 on 2018-04-15 04:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0044_auto_20180414_1645'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='port_of_access_switch',
            options={'ordering': ['access_switch', 'num_in_switch'], 'verbose_name': 'Порт коммутатора доступа', 'verbose_name_plural': 'Порты коммутаторов доступа'},
        ),
        migrations.AddField(
            model_name='port_type',
            name='is_upstream',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='sw_model',
            name='ports_types',
            field=models.CharField(blank=True, max_length=200, verbose_name='Типы портов по умолчанию'),
        ),
    ]