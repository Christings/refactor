# Generated by Django 2.0.1 on 2018-08-21 05:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fanyi', '0008_auto_20180821_0915'),
    ]

    operations = [
        migrations.AddField(
            model_name='gpumonitor',
            name='errorlog',
            field=models.TextField(default=''),
        ),
    ]
