from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import LoginForm
from django.contrib.auth import logout
from django.shortcuts import redirect

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