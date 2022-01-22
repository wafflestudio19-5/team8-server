from rest_framework.routers import SimpleRouter

from django.urls import path, include

from review.views import (
    ReviewArticleViewSet,
    ReviewViewSet,
    ReviewUserView,
    )

app_name = "review"
router = SimpleRouter()
router.register("review/article", ReviewArticleViewSet, basename="article_review")  # /api/v1/review/article/
router.register("review/user", ReviewViewSet, basename="review")  # /api/v1/review/user/

urlpatterns = [
    path("", include(router.urls)),
    path(
        "review/user/<int:user_id>/manner/<str:type>/", ReviewUserView.as_view(), name="user_review"
    ),  # /api/v1/review/user/<int:user_id>/manner/<str:type>/
]