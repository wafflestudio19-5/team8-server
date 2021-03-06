# Generated by Django 3.2.6 on 2022-01-06 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=20)),
                ('content', models.CharField(max_length=255)),
                ('category', models.CharField(max_length=20)),
                ('price', models.PositiveBigIntegerField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sold_at', models.DateTimeField(default=None, null=True)),
                ('deleted_at', models.DateTimeField(default=None, null=True)),
            ],
        ),
    ]
