from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from .models import User
from .utils import (
    PASSWORD_MIN_LENGTH,
    PASSWORD_MIN_LENGTH_MESSAGE,
    validate_github_url,
    validate_phone,
)

ABOUT_TEXTAREA_ROWS = 4
ABOUT_TEXTAREA_MAXLENGTH = 256


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Введите пароль"}
        ),
        min_length=PASSWORD_MIN_LENGTH,
        error_messages={
            "min_length": PASSWORD_MIN_LENGTH_MESSAGE,
        },
    )

    class Meta:
        model = User
        fields = ["name", "surname", "email", "password"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Имя"}
            ),
            "surname": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Фамилия"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email"}
            ),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Введите email"}
        ),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Введите пароль"}
        ),
    )

    def __init__(self, *args, **kwargs):
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            try:
                user = User.objects.get(email=email)
                if not user.is_active:
                    raise ValidationError("Ваша учетная запись неактивна.")
            except User.DoesNotExist:
                pass

            self.user = authenticate(email=email, password=password)
            if self.user is None:
                raise ValidationError("Неверный email или пароль.")

        return cleaned_data

    def get_user(self):
        return self.user


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "surname", "avatar", "about", "phone", "github_url"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Имя"}
            ),
            "surname": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Фамилия"}
            ),
            "avatar": forms.FileInput(attrs={"class": "form-control"}),
            "about": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Расскажите о себе...",
                    "rows": ABOUT_TEXTAREA_ROWS,
                    "maxlength": ABOUT_TEXTAREA_MAXLENGTH,
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+7XXXXXXXXXX или 8XXXXXXXXXX",
                }
            ),
            "github_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://github.com/username",
                }
            ),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        return validate_phone(phone, instance=self.instance)

    def clean_github_url(self):
        github_url = self.cleaned_data.get("github_url")
        return validate_github_url(github_url)


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        label="Текущий пароль",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Введите текущий пароль"}
        ),
    )
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Введите новый пароль"}
        ),
        min_length=PASSWORD_MIN_LENGTH,
        error_messages={
            "min_length": PASSWORD_MIN_LENGTH_MESSAGE,
        },
    )
    new_password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Подтвердите новый пароль"}
        ),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get("old_password")
        if not self.user.check_password(old_password):
            raise ValidationError("Неверный текущий пароль.")
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError({"new_password2": "Новые пароли не совпадают."})

            old_password = cleaned_data.get("old_password")
            if old_password and new_password1 == old_password:
                raise ValidationError(
                    {"new_password1": "Новый пароль должен отличаться от текущего."}
                )

        return cleaned_data

    def save(self):
        self.user.set_password(self.cleaned_data["new_password1"])
        self.user.save()
        return self.user