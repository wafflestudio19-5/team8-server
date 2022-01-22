from rest_framework.routers import SimpleRouter

from django.urls import path, include

from review.views import (
    ReviewArticleViewSet,
    #ReviewUserViewSet,
    )

app_name = "review"
router = SimpleRouter()
router.register("review/article", ReviewArticleViewSet, basename="article_review")  # /api/v1/review/article/
#router.register("review/user", ReviewUserViewSet, basename="user_review")  # /api/v1/user/article/

urlpatterns = [
    path("", include(router.urls)),
]