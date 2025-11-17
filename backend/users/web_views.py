from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import LoginForm, UserEditForm
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages

class UserLoginView(LoginView):
    template_name = "users/login.html"
    authentication_form = LoginForm

def logout_view(request):
    logout(request)
    return redirect("login")

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["user"] = self.request.user
        return ctx

from django.views.generic import ListView
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.views.generic.edit import FormView, UpdateView
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.views import View

class UsersListView(LoginRequiredMixin, ListView):
    model = get_user_model()
    template_name = "users/list.html"
    context_object_name = "users"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_manager:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

class RestoreView(TemplateView):
    template_name = "users/restore.html"

class ChangePasswordView(LoginRequiredMixin, FormView):
    template_name = "users/change_password.html"
    form_class = PasswordChangeForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, self.request.user)
        messages.success(self.request, "Пароль успешно изменён")
        return redirect("profile")

class ChangeRoleView(LoginRequiredMixin, View):
    def get(self, request, role):
        user = request.user
        user.role = role
        user.save(update_fields=["role"])
        messages.success(request, "Роль обновлена")
        return redirect("profile")

class ProfileEditView(LoginRequiredMixin, UpdateView):
    template_name = "users/profile.html"
    form_class = UserEditForm

    def get_object(self, queryset=None):
        return self.request.user

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not self.request.user.is_manager:
            form.fields.pop("role", None)
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["user"] = self.request.user
        ctx["edit_mode"] = True
        return ctx

    def get_success_url(self):
        from django.urls import reverse_lazy
        messages.success(self.request, "Профиль обновлён")
        return reverse_lazy("profile")

class UserEditView(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    template_name = "users/profile.html"
    form_class = UserEditForm

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_manager:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_user_model().objects.get(pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["user"] = self.object
        ctx["edit_mode"] = True
        ctx["is_other"] = True
        return ctx

    def get_success_url(self):
        from django.urls import reverse_lazy
        messages.success(self.request, "Данные пользователя обновлены")
        return reverse_lazy("users_list")