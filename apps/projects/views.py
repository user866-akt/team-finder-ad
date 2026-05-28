import json
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, Http404

from .models import Project, Skill
from .forms import ProjectForm


class JsonRequestMixin:
    def get_json_data(self, request):
        try:
            return json.loads(request.body)
        except (json.JSONDecodeError, AttributeError):
            return {}


class ProjectListView(ListView):
    model = Project
    template_name = "projects/project_list.html"
    paginate_by = 12
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        skill_filter = self.request.GET.get("skill")
        if skill_filter:
            queryset = queryset.filter(skills__name=skill_filter)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["all_skills"] = Skill.objects.values_list("name", flat=True).order_by(
            "name"
        )
        context["active_skill"] = self.request.GET.get("skill", "")
        context["query_prefix"] = (
            f"skill={context['active_skill']}&" if context["active_skill"] else ""
        )
        return context


class ProjectDetailView(DetailView):
    model = Project
    template_name = "projects/project-details.html"
    context_object_name = "project"


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/create-project.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = False
        return context

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        self.object.participants.add(self.request.user)
        messages.success(self.request, "Проект успешно создан!")
        return response

    def get_success_url(self):
        return reverse("projects:project_detail", kwargs={"pk": self.object.pk})


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/create-project.html"

    def test_func(self):
        return self.request.user == self.get_object().owner

    def handle_no_permission(self):
        messages.error(self.request, "У вас нет прав для редактирования этого проекта.")
        return redirect("projects:project_detail", pk=self.get_object().pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context

    def get_success_url(self):
        messages.success(self.request, "Проект успешно обновлён!")
        return reverse("projects:project_detail", kwargs={"pk": self.object.pk})


class SkillAutocompleteView(View):
    def get(self, request):
        query = request.GET.get("q", "").strip()
        if not query:
            return JsonResponse([], safe=False)

        skills = Skill.objects.filter(name__istartswith=query).order_by("name")[:10]

        return JsonResponse([{"id": s.id, "name": s.name} for s in skills], safe=False)


class AddSkillToProjectView(LoginRequiredMixin, JsonRequestMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)

        if request.user != project.owner:
            return JsonResponse({"error": "Нет прав"}, status=403)

        data = self.get_json_data(request)
        skill_id = data.get("skill_id")
        name = data.get("name")

        try:
            if skill_id:
                skill = get_object_or_404(Skill, pk=skill_id)
                created = False
            elif name:
                skill, created = Skill.objects.get_or_create(name=name.strip())
            else:
                return JsonResponse({"error": "Нужен skill_id или name"}, status=400)
            response_data = {
                "id": skill.id,
                "skill_id": skill.id,
                "name": skill.name,
                "created": created,
                "added": not project.skills.filter(id=skill.id).exists(),
            }

            if not response_data["added"]:
                return JsonResponse(response_data)

            project.skills.add(skill)
            response_data["added"] = True
            return JsonResponse(response_data)

        except Http404:
            return JsonResponse({"error": "Навык не найден"}, status=404)


class RemoveSkillFromProjectView(LoginRequiredMixin, View):
    def post(self, request, pk, skill_pk):
        project = get_object_or_404(Project, pk=pk)
        skill = get_object_or_404(Skill, pk=skill_pk)

        if request.user != project.owner:
            return JsonResponse({"error": "Нет прав"}, status=403)

        if not project.skills.filter(id=skill.id).exists():
            return JsonResponse({"error": "Навык не в проекте"}, status=400)

        project.skills.remove(skill)
        return JsonResponse({"status": "ok"})


class ToggleParticipateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)

        if not project.is_open:
            return JsonResponse(
                {"status": "error", "message": "Проект закрыт"}, status=400
            )

        if project.participants.filter(id=request.user.id).exists():
            project.participants.remove(request.user)
            participating = False
        else:
            project.participants.add(request.user)
            participating = True

        return JsonResponse({"status": "ok", "participant": participating})


class CompleteProjectView(LoginRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)

        if request.user != project.owner:
            return JsonResponse({"status": "error"}, status=403)

        if not project.is_open:
            return JsonResponse(
                {"status": "error", "message": "Уже завершён"}, status=400
            )

        project.status = "closed"
        project.save()
        return JsonResponse({"status": "ok", "project_status": "closed"})
