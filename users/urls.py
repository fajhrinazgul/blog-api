from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView, TokenVerifyView

from users import views

urlpatterns = [
    path("api/users/", views.UserListView.as_view(), name="user-list"),
    path(
        "api/users/<str:username>/", views.UserDetailView.as_view(), name="user-detail"
    ),
    path("api/token/", TokenObtainPairView.as_view(), name="token-obtain-vair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/register/", views.RegisterView.as_view(), name="register"),
    path("api/checkuser/", views.CheckCurrentUserView.as_view(), name="check-user"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token-verify"),
]
