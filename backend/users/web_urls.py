from django.urls import path
from .web_views import UserLoginView, logout_view, ProfileView, UsersListView, RestoreView

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("users/", UsersListView.as_view(), name="users_list"),
    path("restore/", RestoreView.as_view(), name="restore"),
]