from rest_framework.routers import SimpleRouter

from django.urls import path, include

from location.views import LocationView, NeighborhoodView

app_name = "location"
router = SimpleRouter()

urlpatterns = [
    path("location/", LocationView.as_view(), name="location"),  # /api/v1/location/
    path(
        "location/<str:location_code>/neighborhood/",
        NeighborhoodView.as_view(),
        name="neighborhood",
    ),  # /api/v1/location/{location_code}/neighborhood/
    path("", include(router.urls)),
]
