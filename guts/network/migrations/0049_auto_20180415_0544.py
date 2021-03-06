# Generated by Django 2.0.2 on 2018-04-15 05:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0048_auto_20180415_0524'),
    ]

    operations = [
        migrations.AlterField(
            model_name='port_type',
            name='id',
            field=models.IntegerField(max_length=10, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='sw_model',
            name='ports_types',
            field=models.CharField(blank=True, help_text='0-Upstream, 1-Branch, 100-Особый порт, 20-Signal, 21-KTV-приемник, 50-PPPoE-клиент, 51-IPoE-клиент, 52-WiFi-HotSpot, 53-WiFi-P2P, 99-Неисправный порт', max_length=200, verbose_name='Типы портов по умолчанию'),
        ),
    ]
