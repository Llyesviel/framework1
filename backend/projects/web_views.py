from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.urls import reverse_lazy
from django.db.models import Count
from users.models import User
from users.permissions import IsManager
from .models import Project, Stage, BuildObject
from .forms import ProjectForm, StageForm, BuildObjectForm
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.views import View
from django.http import HttpResponse
import csv
from defects.models import Defect
from django.http import HttpResponse
import csv
from defects.models import Defect

class ManagerRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_manager:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "projects/list.html"
    context_object_name = "projects"

    def get_queryset(self):
        qs = Project.objects.annotate(defects_count=Count("defects"))
        user = self.request.user
        if user.is_manager:
            pass
        elif user.is_engineer:
            qs = qs.filter(members=user)
        status = self.request.GET.get("status")
        q = self.request.GET.get("q")
        if status in (Project.STATUS_ACTIVE, Project.STATUS_CLOSED):
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(title__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            ct = ContentType.objects.get_for_model(Project)
            entries = (
                LogEntry.objects.filter(content_type_id=ct.id)
                .order_by("-action_time")[:10]
            )
            action_map = {1: "создан проект", 2: "отредактирован проект", 3: "удалён проект"}
            recent = [
                {
                    "time": timezone.localtime(e.action_time).strftime("%H:%M"),
                    "ts": int(e.action_time.timestamp()),
                    "text": f"{action_map.get(e.action_flag, 'действие')} {e.object_repr}",
                }
                for e in entries
            ]
            ctx["recent_actions"] = recent
        except Exception:
            ctx["recent_actions"] = []
        return ctx

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = "projects/detail.html"
    context_object_name = "project"

class ProjectCreateView(ManagerRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/create.html"
    success_url = reverse_lazy("projects_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        LogEntry.objects.log_action(
            user_id=self.request.user.pk,
            content_type_id=ContentType.objects.get_for_model(Project).pk,
            object_id=self.object.pk,
            object_repr=str(self.object),
            action_flag=ADDITION,
            change_message="created",
        )
        messages.success(self.request, "Проект успешно создан")
        return response

class ProjectUpdateView(ManagerRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/edit.html"
    success_url = reverse_lazy("projects_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        LogEntry.objects.log_action(
            user_id=self.request.user.pk,
            content_type_id=ContentType.objects.get_for_model(Project).pk,
            object_id=self.object.pk,
            object_repr=str(self.object),
            action_flag=CHANGE,
            change_message="updated",
        )
        messages.success(self.request, "Проект успешно сохранён")
        return response

class StageCreateView(ManagerRequiredMixin, CreateView):
    model = Stage
    form_class = StageForm
    template_name = "projects/stage_create.html"

    def form_valid(self, form):
        project_id = self.kwargs.get("pk")
        form.instance.project_id = project_id
        messages.success(self.request, "Этап успешно создан")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("project_detail", kwargs={"pk": self.kwargs.get("pk")})

class StageUpdateView(ManagerRequiredMixin, UpdateView):
    model = Stage
    form_class = StageForm
    template_name = "projects/stage_edit.html"

    def get_success_url(self):
        return reverse_lazy("project_detail", kwargs={"pk": self.object.project_id})

    def form_valid(self, form):
        messages.success(self.request, "Этап успешно сохранён")
        return super().form_valid(form)

class ProjectDeleteView(ManagerRequiredMixin, DeleteView):
    model = Project
    template_name = "projects/confirm_delete.html"
    success_url = reverse_lazy("projects_list")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        obj_pk = self.object.pk
        obj_repr = str(self.object)
        ct_id = ContentType.objects.get_for_model(Project).pk
        response = super().delete(request, *args, **kwargs)
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ct_id,
            object_id=obj_pk,
            object_repr=obj_repr,
            action_flag=DELETION,
            change_message="deleted",
        )
        return response

class SingleProjectDefectsExportMixin:
    def defects_queryset(self, request, pk):
        qs = Defect.objects.select_related("project", "performer").filter(project_id=pk)
        return qs.order_by("-created_at")

class ProjectDefectsExportCSVView(LoginRequiredMixin, SingleProjectDefectsExportMixin, View):
    def get(self, request, pk):
        qs = self.defects_queryset(request, pk)
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f"attachment; filename=project_{pk}_defects.csv"
        resp.write("\ufeff")
        writer = csv.writer(resp, delimiter=';')
        writer.writerow(["Проект", "Название дефекта", "Статус", "Приоритет", "Исполнитель", "Срок"])
        for d in qs:
            writer.writerow([
                d.project.title,
                d.title,
                d.get_status_display(),
                d.get_priority_display(),
                (d.performer.username if d.performer else ""),
                (d.deadline.isoformat() if d.deadline else ""),
            ])
        return resp

class ProjectDefectsExportExcelView(LoginRequiredMixin, SingleProjectDefectsExportMixin, View):
    def get(self, request, pk):
        qs = self.defects_queryset(request, pk)
        resp = HttpResponse(content_type="application/vnd.ms-excel")
        resp["Content-Disposition"] = f"attachment; filename=project_{pk}_defects.xls"
        resp.write("\ufeff")
        writer = csv.writer(resp, delimiter=';')
        writer.writerow(["Проект", "Название дефекта", "Статус", "Приоритет", "Исполнитель", "Срок"])
        for d in qs:
            writer.writerow([
                d.project.title,
                d.title,
                d.get_status_display(),
                d.get_priority_display(),
                (d.performer.username if d.performer else ""),
                (d.deadline.isoformat() if d.deadline else ""),
            ])
        return resp

class ProjectExportCSVView(LoginRequiredMixin, View):
    def get(self, request, pk):
        proj = Project.objects.get(pk=pk)
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f"attachment; filename=project_{pk}.csv"
        resp.write("\ufeff")
        writer = csv.writer(resp, delimiter=';')
        writer.writerow(["Название", "Статус", "Дата начала", "Дата окончания", "Описание"])
        writer.writerow([
            proj.title,
            proj.get_status_display(),
            (proj.start_date.isoformat() if proj.start_date else ""),
            (proj.end_date.isoformat() if proj.end_date else ""),
            (proj.description or ""),
        ])
        return resp

class ProjectExportExcelView(LoginRequiredMixin, View):
    def get(self, request, pk):
        proj = Project.objects.get(pk=pk)
        resp = HttpResponse(content_type="application/vnd.ms-excel")
        resp["Content-Disposition"] = f"attachment; filename=project_{pk}.xls"
        resp.write("\ufeff")
        writer = csv.writer(resp, delimiter=';')
        writer.writerow(["Название", "Статус", "Дата начала", "Дата окончания", "Описание"])
        writer.writerow([
            proj.title,
            proj.get_status_display(),
            (proj.start_date.isoformat() if proj.start_date else ""),
            (proj.end_date.isoformat() if proj.end_date else ""),
            (proj.description or ""),
        ])
        return resp

class ProjectsDefectsExportMixin:
    def filtered_projects(self, request):
        qs = Project.objects.all()
        user = request.user
        if getattr(user, "is_engineer", False):
            qs = qs.filter(members=user)
        status = request.GET.get("status")
        q = request.GET.get("q")
        if status in (Project.STATUS_ACTIVE, Project.STATUS_CLOSED):
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(title__icontains=q)
        return qs

    def defects_queryset(self, request):
        pqs = self.filtered_projects(request)
        qs = Defect.objects.select_related("project", "performer").filter(project__in=pqs)
        return qs.order_by("project__title", "-created_at")

class ProjectsDefectsExportCSVView(LoginRequiredMixin, ProjectsDefectsExportMixin, View):
    def get(self, request):
        qs = self.defects_queryset(request)
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = "attachment; filename=projects_defects.csv"
        resp.write("\ufeff")
        writer = csv.writer(resp, delimiter=';')
        writer.writerow(["Проект", "Статус проекта", "Название дефекта", "Статус дефекта", "Приоритет", "Исполнитель", "Срок"])
        for d in qs:
            writer.writerow([
                d.project.title,
                d.project.get_status_display(),
                d.title,
                d.get_status_display(),
                d.get_priority_display(),
                (d.performer.username if d.performer else ""),
                (d.deadline.isoformat() if d.deadline else ""),
            ])
        return resp

class ProjectsDefectsExportExcelView(LoginRequiredMixin, ProjectsDefectsExportMixin, View):
    def get(self, request):
        qs = self.defects_queryset(request)
        resp = HttpResponse(content_type="application/vnd.ms-excel")
        resp["Content-Disposition"] = "attachment; filename=projects_defects.xls"
        resp.write("\ufeff")
        writer = csv.writer(resp, delimiter=';')
        writer.writerow(["Проект", "Статус проекта", "Название дефекта", "Статус дефекта", "Приоритет", "Исполнитель", "Срок"])
        for d in qs:
            writer.writerow([
                d.project.title,
                d.project.get_status_display(),
                d.title,
                d.get_status_display(),
                d.get_priority_display(),
                (d.performer.username if d.performer else ""),
                (d.deadline.isoformat() if d.deadline else ""),
            ])
        return resp

class BuildObjectCreateView(ManagerRequiredMixin, CreateView):
    model = BuildObject
    form_class = BuildObjectForm
    template_name = "projects/object_create.html"

    def form_valid(self, form):
        form.instance.project_id = self.kwargs.get("pk")
        messages.success(self.request, "Объект успешно создан")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("project_detail", kwargs={"pk": self.kwargs.get("pk")})
class ProjectsExportCSVView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Project.objects.annotate(defects_count=Count("defects"))
        user = request.user
        if getattr(user, "is_manager", False):
            pass
        elif getattr(user, "is_engineer", False):
            qs = qs.filter(members=user)
        status = request.GET.get("status")
        q = request.GET.get("q")
        if status in (Project.STATUS_ACTIVE, Project.STATUS_CLOSED):
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(title__icontains=q)
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = "attachment; filename=projects.csv"
        resp.write("\ufeff")
        writer = csv.writer(resp, delimiter=';')
        writer.writerow(["Название", "Статус", "Дата начала", "Дата окончания", "Описание", "Дефектов"])
        for p in qs:
            writer.writerow([
                p.title,
                p.get_status_display(),
                (p.start_date.isoformat() if p.start_date else ""),
                (p.end_date.isoformat() if p.end_date else ""),
                (p.description or ""),
                p.defects_count,
            ])
        return resp

class ProjectsExportExcelView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Project.objects.annotate(defects_count=Count("defects"))
        user = request.user
        if getattr(user, "is_manager", False):
            pass
        elif getattr(user, "is_engineer", False):
            qs = qs.filter(members=user)
        status = request.GET.get("status")
        q = request.GET.get("q")
        if status in (Project.STATUS_ACTIVE, Project.STATUS_CLOSED):
            qs = qs.filter(status=status)
        if q:
            qs = qs.filter(title__icontains=q)
        resp = HttpResponse(content_type="application/vnd.ms-excel")
        resp["Content-Disposition"] = "attachment; filename=projects.xls"
        resp.write("\ufeff")
        writer = csv.writer(resp, delimiter=';')
        writer.writerow(["Название", "Статус", "Дата начала", "Дата окончания", "Описание", "Дефектов"])
        for p in qs:
            writer.writerow([
                p.title,
                p.get_status_display(),
                (p.start_date.isoformat() if p.start_date else ""),
                (p.end_date.isoformat() if p.end_date else ""),
                (p.description or ""),
                p.defects_count,
            ])
        return resp