from http import HTTPStatus

from django.http import JsonResponse

from .models import Project, Skill

ERROR_PROJECT_NOT_FOUND = "Проект не найден"
ERROR_SKILL_NOT_FOUND = "Навык не найден"


def get_project_or_json(pk):
    project = Project.objects.filter(pk=pk).first()
    if project is None:
        return None, JsonResponse(
            {"error": ERROR_PROJECT_NOT_FOUND},
            status=HTTPStatus.NOT_FOUND,
        )
    return project, None


def get_skill_or_json(skill_pk):
    skill = Skill.objects.filter(pk=skill_pk).first()
    if skill is None:
        return None, JsonResponse(
            {"error": ERROR_SKILL_NOT_FOUND},
            status=HTTPStatus.NOT_FOUND,
        )
    return skill, None