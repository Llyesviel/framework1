from django.urls import path
from .web_views import ReportDashboardView, ReportExportView, ProjectReportView, EngineerReportView

urlpatterns = [
    path("dashboard/", ReportDashboardView.as_view(), name="reports_dashboard"),
    path("export/", ReportExportView.as_view(), name="reports_export"),
    path("by_project/", ProjectReportView.as_view(), name="reports_by_project"),
    path("by_engineer/", EngineerReportView.as_view(), name="reports_by_engineer"),
]