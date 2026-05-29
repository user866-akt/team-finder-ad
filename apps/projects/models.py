from django.conf import settings
from django.db import models


SKILL_NAME_MAX_LENGTH = 124

PROJECT_NAME_MAX_LENGTH = 200
PROJECT_GITHUB_URL_MAX_LENGTH = 200
PROJECT_STATUS_MAX_LENGTH = 6

PROJECT_STATUS_OPEN = "open"
PROJECT_STATUS_CLOSED = "closed"

PROJECT_STATUS_CHOICES = [
    (PROJECT_STATUS_OPEN, "Открыт"),
    (PROJECT_STATUS_CLOSED, "Закрыт"),
]


class Skill(models.Model):
    name = models.CharField(
        verbose_name="Название навыка",
        max_length=SKILL_NAME_MAX_LENGTH,
        unique=True,
        error_messages={
            "unique": "Навык с таким названием уже существует.",
        },
    )

    class Meta:
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(
        verbose_name="Название проекта",
        max_length=PROJECT_NAME_MAX_LENGTH,
    )
    description = models.TextField(
        verbose_name="Описание проекта",
        blank=True,
        default="",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        verbose_name="Автор проекта",
    )
    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True,
    )
    github_url = models.URLField(
        verbose_name="Ссылка на GitHub",
        max_length=PROJECT_GITHUB_URL_MAX_LENGTH,
        blank=True,
        default="",
    )
    status = models.CharField(
        verbose_name="Статус",
        max_length=PROJECT_STATUS_MAX_LENGTH,
        choices=PROJECT_STATUS_CHOICES,
        default=PROJECT_STATUS_OPEN,
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="participated_projects",
        verbose_name="Участники проекта",
        blank=True,
    )
    skills = models.ManyToManyField(
        Skill,
        related_name="projects",
        verbose_name="Необходимые навыки",
        blank=True,
    )

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def is_open(self):
        return self.status == PROJECT_STATUS_OPEN

    def toggle_participant(self, user):
        if self.participants.filter(id=user.id).exists():
            self.participants.remove(user)
            return False
        self.participants.add(user)
        return True