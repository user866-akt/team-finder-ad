import hashlib
import random
import re
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import URLValidator
from django.db import models
from PIL import Image, ImageDraw, ImageFont


AVATAR_SIZE = 200
AVATAR_FONT_SIZE = 100
AVATAR_TEXT_COLOR = (255, 255, 255)
AVATAR_FILENAME_PREFIX = "avatar_"
AVATAR_UPLOAD_DIR = "avatars/"
DEFAULT_AVATAR_PATH = "images/default_avatar.png"
AVATAR_HASH_LENGTH = 10
AVATAR_TEXT_OFFSET_Y = 10
AVATAR_IMAGE_FORMAT = "PNG"

COLOR_SOFT_BLUE = (102, 126, 234)
COLOR_SOFT_PINK = (240, 147, 251)
COLOR_SOFT_GREEN = (118, 200, 147)
COLOR_SOFT_GOLD = (230, 195, 105)
COLOR_SOFT_PEACH = (214, 137, 137)
COLOR_SOFT_CYAN = (130, 200, 213)

AVATAR_BACKGROUND_COLORS = [
    COLOR_SOFT_BLUE,
    COLOR_SOFT_PINK,
    COLOR_SOFT_GREEN,
    COLOR_SOFT_GOLD,
    COLOR_SOFT_PEACH,
    COLOR_SOFT_CYAN,
]

FONT_PATHS = [
    "arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arial.ttf",
]

PHONE_PREFIX_PLUS_7 = "+7"
PHONE_PREFIX_8 = "8"
PHONE_DIGITS_COUNT = 10
PHONE_REGEX_PATTERN = r"^(\+7|8)\d{10}$"

GITHUB_DOMAIN = "github.com"

PHONE_INVALID_FORMAT_MESSAGE = (
    "Номер телефона должен быть в формате +7XXXXXXXXXX или 8XXXXXXXXXX"
    " (11 цифр после префикса)."
)
PHONE_NOT_UNIQUE_MESSAGE = "Пользователь с таким номером телефона уже существует."
GITHUB_INVALID_URL_MESSAGE = "Введите корректный URL."
GITHUB_NOT_GITHUB_MESSAGE = "Ссылка должна вести на GitHub (github.com)."

PASSWORD_MIN_LENGTH = 8
PASSWORD_MIN_LENGTH_MESSAGE = "Пароль должен содержать минимум 8 символов."


def generate_default_avatar(name, email):
    letter = name[0].upper() if name else "U"
    bg_color = random.choice(AVATAR_BACKGROUND_COLORS)

    image = Image.new("RGB", (AVATAR_SIZE, AVATAR_SIZE), color=bg_color)
    draw = ImageDraw.Draw(image)
    font = _load_font(AVATAR_FONT_SIZE)

    bbox = draw.textbbox((0, 0), letter, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (AVATAR_SIZE - text_width) / 2
    y = (AVATAR_SIZE - text_height) / 2 - AVATAR_TEXT_OFFSET_Y

    draw.text((x, y), letter, fill=AVATAR_TEXT_COLOR, font=font)

    buffer = BytesIO()
    image.save(buffer, format=AVATAR_IMAGE_FORMAT)
    buffer.seek(0)

    filename = (
        f"{AVATAR_FILENAME_PREFIX}"
        f"{hashlib.md5(email.encode()).hexdigest()[:AVATAR_HASH_LENGTH]}.png"
    )
    return ContentFile(buffer.read(), name=filename)


def _load_font(font_size):
    for font_path in FONT_PATHS:
        try:
            return ImageFont.truetype(font_path, font_size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def validate_phone(phone, instance=None):
    if not phone:
        return phone

    phone = phone.strip()

    if not re.match(PHONE_REGEX_PATTERN, phone):
        raise ValidationError(PHONE_INVALID_FORMAT_MESSAGE)

    if phone.startswith(PHONE_PREFIX_8):
        phone = PHONE_PREFIX_PLUS_7 + phone[1:]

    normalized_8 = PHONE_PREFIX_8 + phone[2:]
    from .models import User
    existing_users = User.objects.filter(
        models.Q(phone=phone) | models.Q(phone=normalized_8)
    )

    if instance and instance.pk:
        existing_users = existing_users.exclude(pk=instance.pk)

    if existing_users.exists():
        raise ValidationError(PHONE_NOT_UNIQUE_MESSAGE)

    return phone


def validate_github_url(github_url):
    if not github_url:
        return github_url

    validator = URLValidator()
    try:
        validator(github_url)
    except ValidationError:
        raise ValidationError(GITHUB_INVALID_URL_MESSAGE)

    if GITHUB_DOMAIN not in github_url.lower():
        raise ValidationError(GITHUB_NOT_GITHUB_MESSAGE)

    return github_url