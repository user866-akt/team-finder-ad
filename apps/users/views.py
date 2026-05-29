from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages

from .models import User
from .forms import RegisterForm, LoginForm, UserEditForm, PasswordChangeForm

USERS_PER_PAGE = 12

class RegisterView(View):
    template_name = "users/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("projects:project_list")
        form = RegisterForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация прошла успешно!")
            return redirect("projects:project_list")
        return render(request, self.template_name, {"form": form})


class LoginView(View):
    template_name = "users/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("projects:project_list")
        form = LoginForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Добро пожаловать, {user.name}!")
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)
            return redirect("projects:project_list")
        return render(request, self.template_name, {"form": form})


class LogoutView(View):
    def get(self, request):
        if request.user.is_authenticated:
            logout(request)
            messages.info(request, "Вы вышли из системы.")
        return redirect("projects:project_list")


class UserDetailView(DetailView):
    model = User
    template_name = "users/user-details.html"
    context_object_name = "user"


class UserEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = "users/edit_profile.html"
    context_object_name = "user"

    def test_func(self):
        return self.request.user == self.get_object()

    def handle_no_permission(self):
        messages.error(self.request, "У вас нет прав для редактирования этого профиля.")
        return redirect("users:user_detail", pk=self.get_object().pk)

    def get_success_url(self):
        messages.success(self.request, "Профиль успешно обновлён!")
        return reverse("users:user_detail", kwargs={"pk": self.object.pk})


class PasswordChangeView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "users/change_password.html"

    def test_func(self):
        user = get_object_or_404(User, pk=self.kwargs.get("pk"))
        return self.request.user == user

    def handle_no_permission(self):
        messages.error(self.request, "У вас нет прав для изменения пароля.")
        return redirect("users:user_detail", pk=self.kwargs.get("pk"))

    def get(self, request, pk):
        form = PasswordChangeForm(user=request.user)
        return render(request, self.template_name, {"form": form})

    def post(self, request, pk):
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Пароль успешно изменён!")
            return redirect("users:user_detail", pk=user.pk)
        return render(request, self.template_name, {"form": form})


class UserListView(ListView):
    model = User
    template_name = "users/participants.html"
    paginate_by = USERS_PER_PAGE
    ordering = ["-date_joined"]
