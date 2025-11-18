from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView, DeleteView
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.http import HttpResponse
import csv
from django.shortcuts import redirect
from django.db.models import Q
from .models import Defect, Attachment, Comment
from .forms import DefectForm, DefectStatusForm, AttachmentForm, CommentForm, AssignPerformerForm
from .services import change_status
from django.contrib.auth import get_user_model

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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            ct = ContentType.objects.get_for_model(Defect)
            entries = (
                LogEntry.objects.filter(content_type_id=ct.id)
                .order_by("-action_time")[:10]
            )
            action_map = {1: "создан дефект", 2: "отредактирован дефект", 3: "удалён дефект"}
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

    def form_valid(self, form):
        self.object = form.save()
        file = self.request.FILES.get("attachments")
        if file:
            Attachment.objects.create(defect=self.object, file=file)
        LogEntry.objects.log_action(
            user_id=self.request.user.pk,
            content_type_id=ContentType.objects.get_for_model(Defect).pk,
            object_id=self.object.pk,
            object_repr=str(self.object),
            action_flag=ADDITION,
            change_message="created",
        )
        messages.success(self.request, "Дефект успешно создан")
        from django.shortcuts import redirect
        return redirect(self.get_success_url())

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

    def form_valid(self, form):
        self.object = form.save()
        file = self.request.FILES.get("attachments")
        if file:
            Attachment.objects.create(defect=self.object, file=file)
        LogEntry.objects.log_action(
            user_id=self.request.user.pk,
            content_type_id=ContentType.objects.get_for_model(Defect).pk,
            object_id=self.object.pk,
            object_repr=str(self.object),
            action_flag=CHANGE,
            change_message="updated",
        )
        messages.success(self.request, "Дефект успешно сохранён")
        from django.shortcuts import redirect
        return redirect(self.get_success_url())

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

class DefectAssignView(LoginRequiredMixin, RoleMixin, FormView):
    template_name = "defects/assign.html"
    form_class = AssignPerformerForm

    def dispatch(self, request, *args, **kwargs):
        if not self.user_is_manager():
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        defect = Defect.objects.get(pk=self.kwargs.get("pk"))
        User = get_user_model()
        qs = User.objects.filter(role="engineer", is_active=True)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(username__icontains=q)
        form.fields["performer"].queryset = qs
        return form

    def form_valid(self, form):
        defect = Defect.objects.get(pk=self.kwargs.get("pk"))
        defect.performer = form.cleaned_data["performer"]
        defect.save(update_fields=["performer", "updated_at"])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("defect_detail", kwargs={"pk": self.kwargs.get("pk")})

class DefectDeleteView(LoginRequiredMixin, RoleMixin, DeleteView):
    model = Defect
    template_name = "defects/confirm_delete.html"
    success_url = reverse_lazy("defects_list")

    def dispatch(self, request, *args, **kwargs):
        if not self.user_is_manager():
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        obj_pk = self.object.pk
        obj_repr = str(self.object)
        ct_id = ContentType.objects.get_for_model(Defect).pk
        response = super().delete(request, *args, **kwargs)
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ct_id,
            object_id=obj_pk,
            object_repr=obj_repr,
            action_flag=DELETION,
            change_message="deleted",
        )
        messages.success(request, "Дефект удалён")
        return response

class DefectAcceptView(LoginRequiredMixin, RoleMixin, View):
    def post(self, request, pk):
        defect = Defect.objects.get(pk=pk)
        if not self.user_is_engineer() or defect.performer_id != request.user.id:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden()
        try:
            change_status(defect, Defect.STATUS_IN_PROGRESS, request.user)
        except Exception:
            pass
        return redirect("defect_detail", pk=pk)

class DefectSubmitReportView(LoginRequiredMixin, RoleMixin, FormView):
    form_class = CommentForm
    template_name = "defects/detail.html"

    def form_valid(self, form):
        defect = Defect.objects.get(pk=self.kwargs.get("pk"))
        if not self.user_is_engineer() or defect.performer_id != self.request.user.id:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden()
        Comment.objects.create(defect=defect, author=self.request.user, text=form.cleaned_data["text"])
        try:
            change_status(defect, Defect.STATUS_REVIEW, self.request.user)
        except Exception:
            pass
        return redirect("defect_detail", pk=defect.pk)

class DefectExportMixin(RoleMixin):
    def build_queryset(self, request):
        qs = Defect.objects.select_related("project", "stage", "performer")
        user = request.user
        project_id = request.GET.get("project")
        status = request.GET.get("status")
        performer_id = request.GET.get("performer")
        priority = request.GET.get("priority")
        search = request.GET.get("q")
        if user.is_manager:
            pass
        elif user.is_engineer:
            qs = qs.filter(Q(project__members=user) | Q(performer=user))
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

class DefectsExportCSVView(LoginRequiredMixin, DefectExportMixin, View):
    def get(self, request):
        qs = self.build_queryset(request)
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = "attachment; filename=defects.csv"
        resp.write("\ufeff")  # UTF-8 BOM for Excel
        writer = csv.writer(resp, delimiter=';')
        writer.writerow(["Проект", "Название", "Статус", "Приоритет", "Исполнитель", "Срок"]) 
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

class DefectsExportExcelView(LoginRequiredMixin, DefectExportMixin, View):
    def get(self, request):
        qs = self.build_queryset(request)
        resp = HttpResponse(content_type="application/vnd.ms-excel")
        resp["Content-Disposition"] = "attachment; filename=defects.xls"
        resp.write("\ufeff")  # UTF-8 BOM for Excel
        writer = csv.writer(resp, delimiter=';')
        writer.writerow(["Проект", "Название", "Статус", "Приоритет", "Исполнитель", "Срок"]) 
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

class DefectExportCSVView(LoginRequiredMixin, View):
    def get(self, request, pk):
        d = Defect.objects.select_related("project", "performer", "stage").get(pk=pk)
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f"attachment; filename=defect_{pk}.csv"
        resp.write("\ufeff")
        writer = csv.writer(resp, delimiter=';')
        writer.writerow(["Проект", "Название", "Статус", "Приоритет", "Исполнитель", "Срок", "Этап", "Создан", "Описание", "Вложений", "Комментариев"])
        writer.writerow([
            d.project.title,
            d.title,
            d.get_status_display(),
            d.get_priority_display(),
            (d.performer.username if d.performer else ""),
            (d.deadline.isoformat() if d.deadline else ""),
            (d.stage.title if d.stage else ""),
            (d.created_at.isoformat() if hasattr(d, 'created_at') and d.created_at else ""),
            (d.description or ""),
            d.attachments.count(),
            d.comments.count(),
        ])
        return resp

class DefectExportExcelView(LoginRequiredMixin, View):
    def get(self, request, pk):
        d = Defect.objects.select_related("project", "performer", "stage").get(pk=pk)
        resp = HttpResponse(content_type="application/vnd.ms-excel")
        resp["Content-Disposition"] = f"attachment; filename=defect_{pk}.xls"
        resp.write("\ufeff")
        writer = csv.writer(resp, delimiter=';')
        writer.writerow(["Проект", "Название", "Статус", "Приоритет", "Исполнитель", "Срок", "Этап", "Создан", "Описание", "Вложений", "Комментариев"])
        writer.writerow([
            d.project.title,
            d.title,
            d.get_status_display(),
            d.get_priority_display(),
            (d.performer.username if d.performer else ""),
            (d.deadline.isoformat() if d.deadline else ""),
            (d.stage.title if d.stage else ""),
            (d.created_at.isoformat() if hasattr(d, 'created_at') and d.created_at else ""),
            (d.description or ""),
            d.attachments.count(),
            d.comments.count(),
        ])
        return resp