# Generated by Django 2.0.2 on 2018-03-22 07:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0021_auto_20180314_0506'),
    ]

    operations = [
        migrations.AddField(
            model_name='mgs',
            name='mgs_num',
            field=models.IntegerField(default=0),
        ),
    ]
