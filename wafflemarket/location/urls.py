from django.urls import path, include
from rest_framework.routers import SimpleRouter
from location.views import LocationView, NeighborhoodView

app_name = 'location'
router = SimpleRouter()

urlpatterns = [
    path('location/', LocationView.as_view(), name='location'),  # /api/v1/location/
    path('location/neighborhood/', NeighborhoodView.as_view(), name='neighborhood'),  # /api/v1/location/neighborhood/
    path('', include(router.urls))
]