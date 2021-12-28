from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

class LocationView(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request):
        pass

    def post(self, request):
        pass

class NeighborhoodView(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request):
        pass