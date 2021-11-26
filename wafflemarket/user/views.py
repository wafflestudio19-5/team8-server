from django.shortcuts import render

from rest_framework.views import Response, APIView
import os
# Create your views here.


class PingAPI(APIView):
    def get(self, *args, **kwargs):
        return Response({
            'ping': 'pong'
        })
