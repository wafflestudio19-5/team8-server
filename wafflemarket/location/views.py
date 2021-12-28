from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from location.models import Location
from location.serializers import LocationSerializer, NeighborhoodSerializer, UserLocationSerializer, UserLocationValidator

class LocationView(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request):
        pass

    def post(self, request):
        user = request.user
        serializer = UserLocationValidator(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update(user, serializer.validated_data)
        return Response(UserLocationSerializer(user).data, status=status.HTTP_200_OK)

class NeighborhoodView(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request):
        user = request.user
        return Response(NeighborhoodSerializer(user.location.neighborhoods, many=True).data, status=status.HTTP_200_OK)