from rest_framework import serializers, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from location.models import Location
from location.serializers import LocationSerializer, NeighborhoodSerializer, UserLocationSerializer, UserLocationValidator

class LocationView(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    @swagger_auto_schema(responses={200: LocationSerializer})
    # returns current user's location info
    def get(self, request):
        user = request.user
        return Response(LocationSerializer(user.location).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=UserLocationValidator, responses={200: UserLocationSerializer})
    # change currentuser's location info
    def post(self, request):
        user = request.user
        serializer = UserLocationValidator(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(user, serializer.validated_data)
        return Response(UserLocationSerializer(user).data, status=status.HTTP_200_OK)

class NeighborhoodView(APIView):
    permission_classes = (permissions.AllowAny, )

    @swagger_auto_schema(request_body=UserLocationValidator, responses={200: NeighborhoodSerializer(many=True)})
    # returns neighborhood of given location
    def get(self, request):
        serializer = UserLocationValidator(data=request.data)
        serializer.is_valid(raise_exception=True)
        location = Location.objects.get(code=serializer.data.get('location_code'))
        return Response(NeighborhoodSerializer(location.neighborhoods, many=True).data, status=status.HTTP_200_OK)