from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.db.models import Q
from .models import Defect, Attachment, Comment
from .forms import DefectForm, DefectStatusForm, AttachmentForm, CommentForm
from .services import change_status

class RoleMixin:
    def user_is_manager(self):
        return self.request.user.is_authenticated and self.request.user.is_manager
    def user_is_engineer(self):
        return self.request.user.is_authenticated and self.request.user.is_engineer
    def user_is_observer(self):
        return self.request.user.is_authenticated and self.request.user.is_observer

class DefectListView(LoginRequiredMixin, RoleMixin, ListView):
    model = Defect
    template_name = "defects/list.html"
    context_object_name = "defects"

    def get_queryset(self):
        qs = Defect.objects.select_related("project", "stage", "performer")
        user = self.request.user
        project_id = self.request.GET.get("project")
        status = self.request.GET.get("status")
        performer_id = self.request.GET.get("performer")
        priority = self.request.GET.get("priority")
        search = self.request.GET.get("q")
        if user.is_manager:
            pass
        elif user.is_engineer:
            qs = qs.filter(Q(project__members=user) | Q(performer=user))
        else:
            pass
        if project_id:
            qs = qs.filter(project_id=project_id)
        if status:
            qs = qs.filter(status=status)
        if performer_id:
            qs = qs.filter(performer_id=performer_id)
        if priority:
            qs = qs.filter(priority=priority)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
        return qs.order_by("-created_at")

class DefectDetailView(LoginRequiredMixin, RoleMixin, DetailView):
    model = Defect
    template_name = "defects/detail.html"
    context_object_name = "defect"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.user_is_observer():
            return redirect("defect_detail", pk=self.object.pk)
        form = CommentForm(request.POST)
        if form.is_valid():
            Comment.objects.create(defect=self.object, author=request.user, text=form.cleaned_data["text"])
        return redirect("defect_detail", pk=self.object.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["comment_form"] = CommentForm()
        return ctx

class DefectCreateView(LoginRequiredMixin, RoleMixin, CreateView):
    model = Defect
    form_class = DefectForm
    template_name = "defects/create.html"
    success_url = reverse_lazy("defects_list")

    def dispatch(self, request, *args, **kwargs):
        if self.user_is_observer():
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.user_is_engineer():
            form.fields.pop("performer", None)
        if self.user_is_observer():
            for f in list(form.fields.keys()):
                form.fields[f].disabled = True
        return form

class DefectUpdateView(LoginRequiredMixin, RoleMixin, UpdateView):
    model = Defect
    form_class = DefectForm
    template_name = "defects/edit.html"
    success_url = reverse_lazy("defects_list")

    def dispatch(self, request, *args, **kwargs):
        defect = self.get_object()
        if self.user_is_manager():
            return super().dispatch(request, *args, **kwargs)
        if self.user_is_engineer():
            if defect.performer_id != request.user.id:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden()
            return super().dispatch(request, *args, **kwargs)
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.user_is_engineer():
            form.fields.pop("performer", None)
        return form

class DefectStatusUpdateView(LoginRequiredMixin, RoleMixin, FormView):
    template_name = "defects/change_status.html"
    form_class = DefectStatusForm

    def get_success_url(self):
        return reverse_lazy("defect_detail", kwargs={"pk": self.kwargs.get("pk")})

    def form_valid(self, form):
        defect = Defect.objects.get(pk=self.kwargs.get("pk"))
        try:
            change_status(defect, form.cleaned_data["status"], self.request.user)
        except Exception:
            pass
        return super().form_valid(form)

class AttachmentUploadView(LoginRequiredMixin, RoleMixin, FormView):
    template_name = "defects/upload_attachments.html"
    form_class = AttachmentForm

    def get_success_url(self):
        return reverse_lazy("defect_detail", kwargs={"pk": self.kwargs.get("pk")})

    def form_valid(self, form):
        defect = Defect.objects.get(pk=self.kwargs.get("pk"))
        Attachment.objects.create(defect=defect, file=form.cleaned_data["file"])
        return super().form_valid(form)