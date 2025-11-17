from django.urls import path
from .web_views import UserLoginView, logout_view, ProfileView, UsersListView, RestoreView, ChangePasswordView, ChangeRoleView, ProfileEditView, UserEditView

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", ProfileEditView.as_view(), name="profile_edit"),
    path("change_password/", ChangePasswordView.as_view(), name="change_password"),
    path("change_role/<str:role>/", ChangeRoleView.as_view(), name="change_role"),
    path("users/", UsersListView.as_view(), name="users_list"),
    path("users/<int:pk>/edit/", UserEditView.as_view(), name="user_edit"),
    path("restore/", RestoreView.as_view(), name="restore"),
]