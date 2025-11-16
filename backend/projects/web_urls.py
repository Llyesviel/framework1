from django.urls import path
from .web_views import (
    ProjectListView,
    ProjectDetailView,
    ProjectCreateView,
    ProjectUpdateView,
    StageCreateView,
    StageUpdateView,
)

urlpatterns = [
    path("", ProjectListView.as_view(), name="projects_list"),
    path("create/", ProjectCreateView.as_view(), name="project_create"),
    path("<int:pk>/", ProjectDetailView.as_view(), name="project_detail"),
    path("<int:pk>/edit/", ProjectUpdateView.as_view(), name="project_edit"),
    path("<int:pk>/stages/create/", StageCreateView.as_view(), name="stage_create"),
    path("stages/<int:pk>/edit/", StageUpdateView.as_view(), name="stage_edit"),
]