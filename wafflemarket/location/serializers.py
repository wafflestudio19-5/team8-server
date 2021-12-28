from rest_framework import serializers
from django.db.models import fields
from django.core.exceptions import ValidationError
from location.models import Location
from user.models import User

class LocationSerializer(serializers.ModelSerializer):
    pass

class NeighborhoodSerializer(serializers.ModelSerializer):
    pass

class UserLocationSerializer(serializers.ModelSerializer):
    pass

class UserLocationValidator(serializers.Serializer):
    pass