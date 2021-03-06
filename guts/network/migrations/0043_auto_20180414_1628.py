# Generated by Django 2.0.2 on 2018-04-14 16:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0042_auto_20180414_1507'),
    ]

    operations = [
        migrations.CreateModel(
            name='PORT_OF_ACCESS_SWITCH',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num_in_switch', models.IntegerField(default=0, editable=False)),
                ('description', models.CharField(blank=True, max_length=100)),
                ('u_vlan', models.CharField(blank=True, max_length=100)),
                ('t_vlans', models.CharField(blank=True, max_length=100)),
            ],
        ),
        migrations.AlterField(
            model_name='access_switch',
            name='ports_count',
            field=models.IntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name='port_of_access_switch',
            name='access_switch',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='network.ACCESS_SWITCH'),
        ),
        migrations.AddField(
            model_name='port_of_access_switch',
            name='type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='network.PORT_TYPE'),
        ),
    ]
