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
    ),  # /api/v1/user/interest/
    path("", include(router.urls)),
]
