# Generated by Django 2.0.2 on 2018-04-06 00:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0037_auto_20180405_0701'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sw_model',
            name='fw_version',
            field=models.CharField(blank=True, max_length=100, verbose_name='Рекомендованная версия ПО'),
        ),
        migrations.AlterField(
            model_name='sw_model',
            name='hw_version',
            field=models.CharField(blank=True, max_length=100, verbose_name='HW версия'),
        ),
        migrations.AlterField(
            model_name='sw_model',
            name='ports_count',
            field=models.IntegerField(default=0, verbose_name='Количество портов'),
        ),
        migrations.AlterField(
            model_name='sw_model',
            name='ports_types',
            field=models.CharField(blank=True, help_text='0-upstream, 1-brn, 20-signal, 21-ktv-reciver, 50-pppoe, 51-ipoe, 52-wifi_hotspot, 53-wifi_p2p, 99-bad', max_length=200, verbose_name='Типы портов по умолчанию'),
        ),
        migrations.AlterField(
            model_name='sw_model',
            name='title',
            field=models.CharField(max_length=100, verbose_name='Название модели'),
        ),
        migrations.AlterField(
            model_name='sw_model',
            name='vendor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='network.VENDORS', verbose_name='Производитель'),
        ),
    ]