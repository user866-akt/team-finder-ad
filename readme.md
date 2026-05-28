# TeamFinder

Платформа для поиска команды для pet-проектов.

## Возможности

- Регистрация и аутентификация пользователей
- Создание и управление проектами
- Просмотр профилей участников
- Присоединение к проектам
- Добавление необходимых навыков к проектам
- Фильтрация проектов по навыкам
- Пагинация на всех страницах

## Технологии

- Python 3.12, Django 5.2
- PostgreSQL 16
- Nginx, Gunicorn
- Docker, Docker Compose
- GitHub Actions (CI)

## Быстрый старт

### 1. Клонировать репозиторий
```bash
git clone <url>
cd team-finder-ad
```

### 2. Создать .env файл
```bash
cp .env_example .env
```
# Отредактируйте .env

### 3. Запустить через Docker
```bash
docker-compose up --build -d
```

### 4. Создать суперпользователя
```bash
docker-compose exec web python manage.py createsuperuser
```

### 5. Открыть в браузере
```text
http://localhost
```

Тестовые пользователи
Email	Пароль
ivan@example.com	password123
maria@example.com	password123
alex@example.com	password123

### Запуск тестов

```bash
docker-compose exec web python manage.py test apps.users apps.projects
```