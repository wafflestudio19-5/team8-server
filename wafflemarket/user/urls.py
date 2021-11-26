from django.urls import path
from .views import PingAPI

urlpatterns = [
    path('ping/', PingAPI.as_view()),
]