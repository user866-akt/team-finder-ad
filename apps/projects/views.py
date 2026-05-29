from http import HTTPStatus

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from team_finder.utils import JsonRequestMixin

from .forms import ProjectForm
from .models import PROJECT_STATUS_CLOSED, Project, Skill

PROJECTS_PER_PAGE = 12
SKILLS_AUTOCOMPLETE_LIMIT = 10

ERROR_NO_PERMISSION = "Нет прав"
ERROR_SKILL_NOT_FOUND = "Навык не найден"
ERROR_NEED_SKILL_ID_OR_NAME = "Нужен skill_id или name"
ERROR_SKILL_NOT_IN_PROJECT = "Навык не в проекте"
ERROR_PROJECT_CLOSED = "Проект закрыт"
ERROR_PROJECT_ALREADY_CLOSED = "Уже завершён"
SUCCESS_SKILL_REMOVED = "ok"


class ProjectListView(ListView):
    model = Project
    template_name = "projects/project_list.html"
    paginate_by = PROJECTS_PER_PAGE
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        skill_filter = self.request.GET.get("skill")
        if skill_filter:
            queryset = queryset.filter(skills__name=skill_filter)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["all_skills"] = (
            Skill.objects.values_list("name", flat=True).order_by("name")
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
        messages.error(
            self.request, "У вас нет прав для редактирования этого проекта."
        )
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

        skills = (
            Skill.objects.filter(name__istartswith=query)
            .order_by("name")[:SKILLS_AUTOCOMPLETE_LIMIT]
        )
        return JsonResponse(
            [{"id": s.id, "name": s.name} for s in skills], safe=False
        )


class AddSkillToProjectView(LoginRequiredMixin, JsonRequestMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)

        if request.user != project.owner:
            return JsonResponse(
                {"error": ERROR_NO_PERMISSION},
                status=HTTPStatus.FORBIDDEN,
            )

        data = self.get_json_data(request)
        skill_id = data.get("skill_id")
        name = data.get("name")

        if skill_id:
            try:
                skill = get_object_or_404(Skill, pk=skill_id)
            except Http404:
                return JsonResponse(
                    {"error": ERROR_SKILL_NOT_FOUND},
                    status=HTTPStatus.NOT_FOUND,
                )
            created = False
        elif name:
            skill, created = Skill.objects.get_or_create(name=name.strip())
        else:
            return JsonResponse(
                {"error": ERROR_NEED_SKILL_ID_OR_NAME},
                status=HTTPStatus.BAD_REQUEST,
            )

        already_added = project.skills.filter(id=skill.id).exists()

        response_data = {
            "id": skill.id,
            "skill_id": skill.id,
            "name": skill.name,
            "created": created,
            "added": not already_added,
        }

        if not already_added:
            project.skills.add(skill)
            response_data["added"] = True

        return JsonResponse(response_data)


class RemoveSkillFromProjectView(LoginRequiredMixin, View):
    def post(self, request, pk, skill_pk):
        project = get_object_or_404(Project, pk=pk)
        skill = get_object_or_404(Skill, pk=skill_pk)

        if request.user != project.owner:
            return JsonResponse(
                {"error": ERROR_NO_PERMISSION},
                status=HTTPStatus.FORBIDDEN,
            )

        if not project.skills.filter(id=skill.id).exists():
            return JsonResponse(
                {"error": ERROR_SKILL_NOT_IN_PROJECT},
                status=HTTPStatus.BAD_REQUEST,
            )

        project.skills.remove(skill)
        return JsonResponse({"status": SUCCESS_SKILL_REMOVED})


class ToggleParticipateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)

        if not project.is_open:
            return JsonResponse(
                {"status": "error", "message": ERROR_PROJECT_CLOSED},
                status=HTTPStatus.BAD_REQUEST,
            )

        is_participant = project.participants.filter(id=request.user.id).exists()

        if is_participant:
            project.participants.remove(request.user)
        else:
            project.participants.add(request.user)

        return JsonResponse({
            "status": "ok",
            "participant": not is_participant,
        })


class CompleteProjectView(LoginRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)

        if request.user != project.owner:
            return JsonResponse(
                {"status": "error"},
                status=HTTPStatus.FORBIDDEN,
            )

        if not project.is_open:
            return JsonResponse(
                {"status": "error", "message": ERROR_PROJECT_ALREADY_CLOSED},
                status=HTTPStatus.BAD_REQUEST,
            )

        project.status = PROJECT_STATUS_CLOSED
        project.save()
        return JsonResponse({
            "status": "ok",
            "project_status": PROJECT_STATUS_CLOSED,
        })