from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import ArticleViewSet

from article import views

app_name = 'article'
router = SimpleRouter()
router.register('article', ArticleViewSet, basename='article')  # /api/v1/article/

urlpatterns = [
    path('', include(router.urls))
]