from django import forms
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'github_url', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название проекта'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Опишите ваш проект...',
                'rows': 5
            }),
            'github_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/username/repo'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'name': 'Название проекта',
            'description': 'Описание проекта',
            'github_url': 'Ссылка на GitHub',
            'status': 'Статус проекта',
        }

    def clean_github_url(self):
        github_url = self.cleaned_data.get('github_url')
        if not github_url:
            return github_url
        validator = URLValidator()
        try:
            validator(github_url)
        except ValidationError:
            raise ValidationError('Введите корректный URL.')
        if 'github.com' not in github_url.lower():
            raise ValidationError('Ссылка должна вести на GitHub (github.com).')
        
        return github_url