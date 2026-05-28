from django.core.management.base import BaseCommand
from apps.users.models import User
from apps.projects.models import Project, Skill


class Command(BaseCommand):
    help = "Создаёт тестовых пользователей и проекты"

    def handle(self, *args, **options):
        if User.objects.filter(email="ivan@example.com").exists():
            self.stdout.write(self.style.WARNING("Тестовые данные уже существуют"))
            return

        python, _ = Skill.objects.get_or_create(name="Python")
        django, _ = Skill.objects.get_or_create(name="Django")
        docker, _ = Skill.objects.get_or_create(name="Docker")
        sql, _ = Skill.objects.get_or_create(name="SQL")
        js, _ = Skill.objects.get_or_create(name="JavaScript")
        self.stdout.write("Навыки созданы")

        user1 = User.objects.create_user(
            email="ivan@example.com",
            name="Иван",
            surname="Петров",
            password="password123",
        )
        user1.about = "Fullstack разработчик, люблю Python и JavaScript"
        user1.phone = "+79001234567"
        user1.github_url = "https://github.com/ivan_petr"
        user1.save()

        project1 = Project.objects.create(
            name="Веб-приложение для заметок",
            description="Веб-приложение для создания и управления заметками с тегами.",
            owner=user1,
            status="open",
        )
        project1.participants.add(user1)
        project1.skills.add(python, django, js)
        self.stdout.write(f"Создан пользователь: {user1.email}")

        user2 = User.objects.create_user(
            email="maria@example.com",
            name="Мария",
            surname="Сидорова",
            password="password123",
        )
        user2.about = "Data Scientist, специализируюсь на ML и анализе данных"
        user2.phone = "+79009876543"
        user2.github_url = "https://github.com/maria_s"
        user2.save()

        project2 = Project.objects.create(
            name="Анализ данных погоды",
            description="Сбор и анализ данных о погоде с использованием Python и SQL.",
            owner=user2,
            status="open",
        )
        project2.participants.add(user2)
        project2.skills.add(python, sql)
        self.stdout.write(f"Создан пользователь: {user2.email}")

        user3 = User.objects.create_user(
            email="alex@example.com",
            name="Алексей",
            surname="Волков",
            password="password123",
        )
        user3.about = "DevOps инженер, контейнеризация и CI/CD"
        user3.phone = "+79005551122"
        user3.github_url = "https://github.com/alex_volkov"
        user3.save()

        project3 = Project.objects.create(
            name="Docker-оркестрация микросервисов",
            description="Настройка Docker Compose для оркестрации микросервисов.",
            owner=user3,
            status="open",
        )
        project3.participants.add(user3)
        project3.skills.add(docker, python)
        self.stdout.write(f"Создан пользователь: {user3.email}")

        self.stdout.write(self.style.SUCCESS("Тестовые данные успешно созданы!"))
