# Generated by Django 2.0.2 on 2018-03-23 07:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0023_auto_20180323_0541'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campus',
            name='mgs',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='network.MGS', verbose_name='МГС'),
        ),
        migrations.AlterField(
            model_name='campus',
            name='title',
            field=models.CharField(max_length=20, unique=True, verbose_name='Название'),
        ),
    ]
