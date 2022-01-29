from rest_framework.routers import SimpleRouter

from django.urls import path, include

from user.views import (
    GoogleSigninCallBackApi,
    UserViewSet,
    UserSignUpView,
    UserLogoutView,
    UserLeaveView,
    UserAuthView,
    UserCategoryView,
    UserLikedView,
    UserHistoryView,
)

app_name = "user"
router = SimpleRouter()
router.register("user", UserViewSet, basename="user")  # /api/v1/user/


urlpatterns = [
    path("signup/", UserSignUpView.as_view(), name="signup"),  # /api/v1/signup/
    path(
        "login/google/", GoogleSigninCallBackApi.as_view(), name="google_login"
    ),  # /api/v1/login/google/
    path(
        "authenticate/", UserAuthView.as_view(), name="authenticate"
    ),  # /api/v1/authenticate/
    path("logout/", UserLogoutView.as_view(), name="logout"),  # /api/v1/logout/
    path("leave/", UserLeaveView.as_view(), name="leave"),  # /api/v1/leave/
    path(
        "user/category/", UserCategoryView.as_view(), name="category"
    ),  # /api/v1/user/category/
    path(
        "user/history/<int:pk>/", UserHistoryView.as_view(), name="history"
    ), # /api/v1/user/history/{id} (구매내역 : 1, 판매내역 : 2)
    path("user/liked/", UserLikedView.as_view(), name="liked"),  # /api/v1/user/likes/
    path("", include(router.urls)),
]
