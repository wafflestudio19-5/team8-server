from django.db import models

class Location(models.Model):
    code = models.CharField(max_length=20, unique=True)
    place_name = models.CharField(max_length=255, unique=True)
    neighbor_relationships = models.ManyToManyField('self', through='LocationNeighborhood', null=True, symmetrical=False)

class LocationNeighborhood(models.Model):
    location = models.ForeignKey(Location, related_name='neighborhoods', on_delete=models.CASCADE)
    neighborhood = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='locations')

    class Meta:
        db_table='location_neighborhood'