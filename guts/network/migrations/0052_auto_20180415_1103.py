# Generated by Django 2.0.2 on 2018-04-15 11:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0051_auto_20180415_0603'),
    ]

    operations = [
        migrations.AlterField(
            model_name='port_of_access_switch',
            name='u_vlan',
            field=models.IntegerField(default=0, verbose_name='Untag-vlan/PVID'),
        ),
    ]