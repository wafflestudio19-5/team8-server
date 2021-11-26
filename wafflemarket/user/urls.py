from django.urls import path
from wafflemarket.user.views import PingAPI

urlpatterns = [
    path('', PingAPI.as_view()),
]