from rest_framework.routers import SimpleRouter
from django.urls import path, include

from article.views import ArticleViewSet, CommentView

app_name = "article"
router = SimpleRouter()
router.register("article", ArticleViewSet, basename="article")  # /api/v1/article/

urlpatterns = [
    path("", include(router.urls)),
    path(
        "article/<int:a_id>/comment/<int:c_id>/", CommentView.as_view(), name="comment"
    ),  # /api/v1/article/<int:a_id>/comment/<int:c_id>/
]
