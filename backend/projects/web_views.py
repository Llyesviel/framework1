from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
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