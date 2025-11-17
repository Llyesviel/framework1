from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import HttpResponse
from users.models import User
from users.permissions import IsManager
from .analytics import summary, by_project, by_engineer
from .analytics import by_day_projects, by_day_defects
import csv

class ManagerRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_manager:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

class ReportDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "reports/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        s = summary()
        ctx["status_labels"] = [i["status"] for i in s["by_status"]]
        ctx["status_counts"] = [i["count"] for i in s["by_status"]]
        ctx["priority_labels"] = [i["priority"] for i in s["by_priority"]]
        ctx["priority_counts"] = [i["count"] for i in s["by_priority"]]
        dp = by_day_projects(7)
        dd = by_day_defects(7)
        # Prefer labels from projects (should match defects range)
        ctx["daily_labels"] = dp["labels"]
        ctx["daily_projects"] = dp["counts"]
        ctx["daily_defects"] = dd["counts"]
        return ctx

class ReportExportView(ManagerRequiredMixin, TemplateView):
    template_name = "reports/export.html"

    def get(self, request, *args, **kwargs):
        if request.GET.get("download") == "csv":
            from defects.models import Defect
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = "attachment; filename=defects.csv"
            writer = csv.writer(response)
            writer.writerow(["id", "project", "stage", "title", "status", "priority", "performer", "deadline"])
            for d in Defect.objects.all().select_related("project", "stage", "performer"):
                writer.writerow([d.id, d.project_id, d.stage_id or "", d.title, d.status, d.priority, d.performer_id or "", d.deadline or ""])
            return response
        return super().get(request, *args, **kwargs)

class ProjectReportView(LoginRequiredMixin, TemplateView):
    template_name = "reports/project_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project_id = int(self.request.GET.get("project_id")) if self.request.GET.get("project_id") else None
        ctx["data"] = by_project(project_id) if project_id else {"project_id": None, "total": 0, "by_status": []}
        return ctx

class EngineerReportView(LoginRequiredMixin, TemplateView):
    template_name = "reports/engineer_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        engineer_id = int(self.request.GET.get("engineer_id")) if self.request.GET.get("engineer_id") else None
        ctx["data"] = by_engineer(engineer_id) if engineer_id else {"engineer_id": None, "total": 0, "by_status": []}
        return ctx