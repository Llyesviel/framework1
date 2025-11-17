from django.urls import path
from .web_views import (
    ProjectListView,
    ProjectDetailView,
    ProjectCreateView,
    ProjectUpdateView,
    StageCreateView,
    StageUpdateView,
    ProjectDeleteView,
    BuildObjectCreateView,
    ProjectDefectsExportCSVView,
    ProjectDefectsExportExcelView,
    ProjectExportCSVView,
    ProjectExportExcelView,
    ProjectsExportCSVView,
    ProjectsExportExcelView,
)

urlpatterns = [
    path("", ProjectListView.as_view(), name="projects_list"),
    path("create/", ProjectCreateView.as_view(), name="project_create"),
    path("<int:pk>/", ProjectDetailView.as_view(), name="project_detail"),
    path("<int:pk>/edit/", ProjectUpdateView.as_view(), name="project_edit"),
    path("<int:pk>/delete/", ProjectDeleteView.as_view(), name="project_delete"),
    path("<int:pk>/stages/create/", StageCreateView.as_view(), name="stage_create"),
    path("stages/<int:pk>/edit/", StageUpdateView.as_view(), name="stage_edit"),
    path("<int:pk>/objects/create/", BuildObjectCreateView.as_view(), name="object_create"),
    path("<int:pk>/export/defects/csv/", ProjectDefectsExportCSVView.as_view(), name="project_defects_export_csv"),
    path("<int:pk>/export/defects/xls/", ProjectDefectsExportExcelView.as_view(), name="project_defects_export_xls"),
    path("<int:pk>/export/csv/", ProjectExportCSVView.as_view(), name="project_export_csv"),
    path("<int:pk>/export/xls/", ProjectExportExcelView.as_view(), name="project_export_xls"),
    path("export/projects/csv/", ProjectsExportCSVView.as_view(), name="projects_export_csv"),
    path("export/projects/xls/", ProjectsExportExcelView.as_view(), name="projects_export_xls"),
]