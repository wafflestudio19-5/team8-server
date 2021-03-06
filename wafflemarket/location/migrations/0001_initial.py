# Generated by Django 3.2.6 on 2022-01-06 15:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, unique=True)),
                ('place_name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='LocationNeighborhood',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='neighborhoods', to='location.location')),
                ('neighborhood', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='locations', to='location.location')),
            ],
            options={
                'db_table': 'location_neighborhood',
            },
        ),
        migrations.AddField(
            model_name='location',
            name='neighbor_relationships',
            field=models.ManyToManyField(through='location.LocationNeighborhood', to='location.Location'),
        ),
    ]
