from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from .managers import CustomUserManager
import hashlib
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
import random


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name="Email адрес",
        max_length=255,
        unique=True,
        error_messages={
            "unique": "Пользователь с таким email уже существует.",
        },
    )
    name = models.CharField(verbose_name="Имя", max_length=124)
    surname = models.CharField(verbose_name="Фамилия", max_length=124)
    avatar = models.ImageField(
        verbose_name="Аватар", upload_to="avatars/", default="images/default_avatar.png"
    )
    phone = models.CharField(
        verbose_name="Номер телефона", max_length=12, blank=True, default=""
    )
    github_url = models.URLField(
        verbose_name="Ссылка на GitHub", max_length=200, blank=True, default=""
    )
    about = models.TextField(
        verbose_name="О себе", max_length=256, blank=True, default=""
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
        verbose_name="Дата регистрации", default=timezone.now
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
        if (
            is_new
            and not self.avatar
            or self.avatar.name == "images/default_avatar.png"
        ):
            self.avatar = self._generate_default_avatar()

        super().save(*args, **kwargs)

    def _generate_default_avatar(self):
        letter = self.name[0].upper() if self.name else "U"
        colors = [
            (102, 126, 234),
            (240, 147, 251),
            (118, 200, 147),
            (230, 195, 105),
            (214, 137, 137),
            (130, 200, 213),
        ]
        bg_color = random.choice(colors)
        img_size = (200, 200)
        image = Image.new("RGB", img_size, color=bg_color)
        draw = ImageDraw.Draw(image)
        font_size = 100
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size
                )
            except IOError:
                try:
                    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
                except IOError:
                    font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), letter, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (img_size[0] - text_width) / 2
        y = (img_size[1] - text_height) / 2 - 10
        draw.text((x, y), letter, fill=(255, 255, 255), font=font)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        filename = f"avatar_{hashlib.md5(self.email.encode()).hexdigest()[:10]}.png"
        return ContentFile(buffer.read(), name=filename)
