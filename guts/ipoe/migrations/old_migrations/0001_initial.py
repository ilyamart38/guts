# Generated by Django 2.0.2 on 2018-03-05 10:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('network', '0001_squashed_0082_auto_20180725_1706'),
        ('clients', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IPOE_SERVICESS',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='clients.CLIENTS')),
                ('sap', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='network.SAP')),
            ],
        ),
    ]
