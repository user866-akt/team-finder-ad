from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import CustomUserManager
from .utils import (
    AVATAR_UPLOAD_DIR,
    DEFAULT_AVATAR_PATH,
    generate_default_avatar,
)

USER_EMAIL_MAX_LENGTH = 255
USER_NAME_MAX_LENGTH = 124
USER_SURNAME_MAX_LENGTH = 124
USER_PHONE_MAX_LENGTH = 12
USER_GITHUB_URL_MAX_LENGTH = 200
USER_ABOUT_MAX_LENGTH = 256


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name="Email адрес",
        max_length=USER_EMAIL_MAX_LENGTH,
        unique=True,
        error_messages={
            "unique": "Пользователь с таким email уже существует.",
        },
    )
    name = models.CharField(
        verbose_name="Имя",
        max_length=USER_NAME_MAX_LENGTH,
    )
    surname = models.CharField(
        verbose_name="Фамилия",
        max_length=USER_SURNAME_MAX_LENGTH,
    )
    avatar = models.ImageField(
        verbose_name="Аватар",
        upload_to=AVATAR_UPLOAD_DIR,
        default=DEFAULT_AVATAR_PATH,
    )
    phone = models.CharField(
        verbose_name="Номер телефона",
        max_length=USER_PHONE_MAX_LENGTH,
        blank=True,
        default="",
    )
    github_url = models.URLField(
        verbose_name="Ссылка на GitHub",
        max_length=USER_GITHUB_URL_MAX_LENGTH,
        blank=True,
        default="",
    )
    about = models.TextField(
        verbose_name="О себе",
        max_length=USER_ABOUT_MAX_LENGTH,
        blank=True,
        default="",
    )
    is_active = models.BooleanField(
        verbose_name="Активный",
        default=True,
    )
    is_staff = models.BooleanField(
        verbose_name="Администратор",
        default=False,
    )
    date_joined = models.DateTimeField(
        verbose_name="Дата регистрации",
        default=timezone.now,
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        return f"{self.name} {self.surname}"

    def get_short_name(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and not self.avatar or self.avatar.name == DEFAULT_AVATAR_PATH:
            self.avatar = generate_default_avatar(self.name, self.email)
        super().save(*args, **kwargs)