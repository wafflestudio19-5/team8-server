# Generated by Django 3.2.6 on 2022-01-17 14:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0006_auto_20220114_2253'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='hit',
            field=models.PositiveBigIntegerField(default=0),
        ),
    ]
