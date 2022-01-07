from rest_framework import serializers
from django.db.models import fields
from django.core.exceptions import ValidationError
from location.models import Location
from user.models import User

# response serializer for [GET]location
class LocationSerializer(serializers.ModelSerializer):

    neighborhoods = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = (
            'place_name',
            'code',
            'neighborhoods'
        )

    def get_neighborhoods(self, location):
        return NeighborhoodSerializer(location.neighborhoods, many=True, context=self.context).data

# location serializer simple ver.
class LocationSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Location
        fields = (
            'place_name',
            'code',
        )

# response serializer for [GET]location/neighborhood
class NeighborhoodSerializer(serializers.ModelSerializer):
    
    place_name = serializers.ReadOnlyField(source='neighborhood.place_name')
    code = serializers.ReadOnlyField(source='neighborhood.code')

    class Meta:
        model = Location
        fields = (
            'place_name',
            'code',
        )

# response serializer for [POST]location
class UserLocationSerializer(serializers.ModelSerializer):

    location = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'username',
            'location',
        )

    def get_location(self, user):
        return user.location.place_name

# request validator for [POST]location
class UserLocationValidator(serializers.Serializer):
    
    location_code = serializers.CharField(required=True)
    
    def validate(self, data):
        location_code = data.get('location_code')
        location = Location.objects.filter(code=location_code)
        if location.count() == 0:
            raise serializers.ValidationError('올바른 지역코드가 아닙니다.')
        data['location'] = location[0]
        return data
    
    def update(self, user, validated_data):
        user.location = validated_data.get('location', user.location)
        user.save()
        return user