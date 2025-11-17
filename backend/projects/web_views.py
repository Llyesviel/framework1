from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Count
from users.models import User
from users.permissions import IsManager
from .models import Project, Stage
from .forms import ProjectForm, StageForm

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
            return qs
        if user.is_engineer:
            return qs.filter(members=user)
        return qs

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = "projects/detail.html"
    context_object_name = "project"

class ProjectCreateView(ManagerRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/create.html"
    success_url = reverse_lazy("projects_list")

class ProjectUpdateView(ManagerRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/edit.html"
    success_url = reverse_lazy("projects_list")

class StageCreateView(ManagerRequiredMixin, CreateView):
    model = Stage
    form_class = StageForm
    template_name = "projects/stage_create.html"

    def form_valid(self, form):
        project_id = self.kwargs.get("pk")
        form.instance.project_id = project_id
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("project_detail", kwargs={"pk": self.kwargs.get("pk")})

class StageUpdateView(ManagerRequiredMixin, UpdateView):
    model = Stage
    form_class = StageForm
    template_name = "projects/stage_edit.html"

    def get_success_url(self):
        return reverse_lazy("project_detail", kwargs={"pk": self.object.project_id})

class ProjectDeleteView(ManagerRequiredMixin, DeleteView):
    model = Project
    template_name = "projects/confirm_delete.html"
    success_url = reverse_lazy("projects_list")