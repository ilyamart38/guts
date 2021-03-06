# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2019-01-03 14:02
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('network', '0023_auto_20181111_2245'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalPORT_OF_ACCESS_SWITCH',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('num_in_switch', models.IntegerField(default=0)),
                ('description', models.CharField(blank=True, max_length=100, null=True)),
                ('port_name', models.CharField(max_length=100)),
                ('u_vlan', models.IntegerField(default=0, verbose_name='Untag-vlan/PVID')),
                ('t_vlans', models.CharField(blank=True, max_length=1000)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('access_switch', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='network.ACCESS_SWITCH')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('port_type', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='network.PORT_TYPE')),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'verbose_name': 'historical Порт коммутатора доступа',
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalSW_MODEL',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='Название модели')),
                ('eqm_type', models.CharField(default='', max_length=100, verbose_name='Тип объекта в eqm')),
                ('fw_version', models.CharField(blank=True, max_length=100, verbose_name='Рекомендованная версия ПО')),
                ('bootrom_file', models.TextField(blank=True, max_length=100, verbose_name='Файл прошивки bootrom')),
                ('transit_fw', models.TextField(blank=True, max_length=100, verbose_name='Файл промежуточной прошивки')),
                ('fw_file', models.TextField(blank=True, max_length=100, verbose_name='Файл прошивки')),
                ('fw_update_commands', models.TextField(blank=True, verbose_name='Описание процесса обновления прошивки')),
                ('hw_version', models.CharField(blank=True, max_length=100, verbose_name='HW версия')),
                ('ports_count', models.IntegerField(default=0, verbose_name='Количество портов')),
                ('ports_names', models.CharField(blank=True, max_length=700, verbose_name='Названия портов в конфиге')),
                ('ports_types', models.CharField(blank=True, help_text='0-Магистральный порт, 1-Распределительный порт, 3-PPPoE-подключение, 4-Прочее-подключение, 5-Сигнализатор, 99-Неисправный порт', max_length=200, verbose_name='Типы портов по умолчанию')),
                ('cfg_template', models.TextField(blank=True, max_length=100, verbose_name='Шаблон конфигурации')),
                ('cfg_download_commands', models.TextField(blank=True, verbose_name='Описание процесса загрузки конфигурации')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('vendor', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='network.VENDORS', verbose_name='Производитель')),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'verbose_name': 'historical Модель коммутаторов',
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
