# Generated by Django 2.0.2 on 2018-03-23 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0029_auto_20180323_1331'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='campus',
            options={'ordering': ('ms', 'num_in_ms'), 'verbose_name': 'Кампус', 'verbose_name_plural': 'Кампусы'},
        ),
        migrations.RemoveField(
            model_name='campus',
            name='title',
        ),
        migrations.AddField(
            model_name='campus',
            name='prefix',
            field=models.CharField(choices=[('ppk', 'ППК'), ('mku', 'МКУ')], default='ppk', max_length=20, unique=True, verbose_name='Название'),
        ),
    ]
