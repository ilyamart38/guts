# Generated by Django 2.0.2 on 2018-03-23 12:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0024_auto_20180323_0716'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='thread',
            name='title',
        ),
        migrations.AlterField(
            model_name='mgs',
            name='mgs_num',
            field=models.IntegerField(default=0, unique=True),
        ),
    ]
