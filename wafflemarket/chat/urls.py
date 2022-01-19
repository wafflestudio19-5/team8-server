from xml.etree.ElementInclude import include
from rest_framework.routers import SimpleRouter

from django.urls import path

from chat.views import ChatRoomViewSet


app_name = "chat"
router = SimpleRouter()
router.register("chat", ChatRoomViewSet, basename="chat")  # /api/v1/user/

urlpatterns = [
    path('', include(router.urls)),
]