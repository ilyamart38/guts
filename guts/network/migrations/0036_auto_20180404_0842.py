# Generated by Django 2.0.2 on 2018-04-04 08:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0035_auto_20180404_0834'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='guts_network',
            options={'verbose_name': 'Подсеть', 'verbose_name_plural': 'Подсети разрешонные в ГУТС.'},
        ),
        migrations.AlterField(
            model_name='guts_network',
            name='network',
            field=models.CharField(max_length=18, unique=True),
        ),
    ]
