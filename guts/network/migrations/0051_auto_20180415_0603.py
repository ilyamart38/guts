# Generated by Django 2.0.2 on 2018-04-15 06:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0050_auto_20180415_0545'),
    ]

    operations = [
        migrations.AlterField(
            model_name='port_of_access_switch',
            name='u_vlan',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='network.VLAN', verbose_name='Untag-vlan/PVID'),
        ),
        migrations.AlterField(
            model_name='port_type',
            name='id',
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
    ]
