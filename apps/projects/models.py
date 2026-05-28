from django.db import models
from django.conf import settings


class Skill(models.Model):
    name = models.CharField(
        verbose_name="Название навыка",
        max_length=124,
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
    STATUS_CHOICES = [
        ("open", "Открыт"),
        ("closed", "Закрыт"),
    ]

    name = models.CharField(verbose_name="Название проекта", max_length=200)
    description = models.TextField(
        verbose_name="Описание проекта", blank=True, default=""
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        verbose_name="Автор проекта",
    )
    created_at = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)
    github_url = models.URLField(
        verbose_name="Ссылка на GitHub", max_length=200, blank=True, default=""
    )
    status = models.CharField(
        verbose_name="Статус", max_length=6, choices=STATUS_CHOICES, default="open"
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="participated_projects",
        verbose_name="Участники проекта",
        blank=True,
    )
    skills = models.ManyToManyField(
        Skill, related_name="projects", verbose_name="Необходимые навыки", blank=True
    )

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def is_open(self):
        return self.status == "open"

    def toggle_participant(self, user):
        if self.participants.filter(id=user.id).exists():
            self.participants.remove(user)
            return False
        else:
            self.participants.add(user)
            return True
