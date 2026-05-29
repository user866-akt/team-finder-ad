import json

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from .models import Project, Skill

User = get_user_model()

TEST_OWNER_EMAIL = "owner@example.com"
TEST_OWNER_PASSWORD = "ownerpass123"
TEST_OWNER_NAME = "Owner"
TEST_OWNER_SURNAME = "User"

TEST_OTHER_EMAIL = "other@example.com"
TEST_OTHER_PASSWORD = "otherpass123"
TEST_OTHER_NAME = "Other"

TEST_USER_EMAIL = "user@example.com"
TEST_USER_PASSWORD = "userpass123"
TEST_USER_NAME = "User"
TEST_USER_SURNAME = "Test"

TEST_PROJECT_NAME = "Test Project"
TEST_PROJECT_DESCRIPTION = "Test description"
TEST_PROJECT_STATUS_OPEN = "open"
TEST_PROJECT_STATUS_CLOSED = "closed"

TEST_SKILL_PYTHON = "Python"
TEST_SKILL_DJANGO = "Django"
TEST_SKILL_REACT = "React"

NEW_PROJECT_NAME = "New Project"
NEW_PROJECT_DESCRIPTION = "New description"
UPDATED_PROJECT_NAME = "Updated Project"
UPDATED_PROJECT_DESCRIPTION = "Updated description"

PAGINATION_COUNT = 12
PAGINATION_CREATE_COUNT = 13

HTTP_OK = 200
HTTP_FOUND = 302
HTTP_FORBIDDEN = 403


class ProjectModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email=TEST_OWNER_EMAIL,
            name=TEST_OWNER_NAME,
            surname=TEST_OWNER_SURNAME,
            password=TEST_OWNER_PASSWORD,
        )
        self.skill = Skill.objects.create(name=TEST_SKILL_PYTHON)

    def test_create_skill(self):
        skill = Skill.objects.create(name=TEST_SKILL_DJANGO)
        self.assertEqual(skill.name, TEST_SKILL_DJANGO)
        self.assertEqual(str(skill), TEST_SKILL_DJANGO)

    def test_skill_unique(self):
        with self.assertRaises(Exception):
            Skill.objects.create(name=TEST_SKILL_PYTHON)

    def test_create_project(self):
        project = Project.objects.create(
            name=TEST_PROJECT_NAME,
            description=TEST_PROJECT_DESCRIPTION,
            owner=self.user,
            status=TEST_PROJECT_STATUS_OPEN,
        )
        project.participants.add(self.user)
        project.skills.add(self.skill)

        self.assertEqual(project.name, TEST_PROJECT_NAME)
        self.assertEqual(project.owner, self.user)
        self.assertEqual(project.status, TEST_PROJECT_STATUS_OPEN)
        self.assertTrue(project.is_open)
        self.assertEqual(project.participants.count(), 1)
        self.assertEqual(project.skills.count(), 1)
        self.assertEqual(str(project), TEST_PROJECT_NAME)

    def test_project_status_closed(self):
        project = Project.objects.create(
            name="Closed Project",
            description="Test",
            owner=self.user,
            status=TEST_PROJECT_STATUS_CLOSED,
        )
        self.assertFalse(project.is_open)


class ProjectViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            email=TEST_OWNER_EMAIL,
            name=TEST_OWNER_NAME,
            surname=TEST_OWNER_SURNAME,
            password=TEST_OWNER_PASSWORD,
        )
        self.other_user = User.objects.create_user(
            email=TEST_OTHER_EMAIL,
            name=TEST_OTHER_NAME,
            surname=TEST_USER_SURNAME,
            password=TEST_OTHER_PASSWORD,
        )
        self.skill1 = Skill.objects.create(name=TEST_SKILL_PYTHON)
        self.skill2 = Skill.objects.create(name=TEST_SKILL_DJANGO)

        self.project = Project.objects.create(
            name=TEST_PROJECT_NAME,
            description=TEST_PROJECT_DESCRIPTION,
            owner=self.owner,
            status=TEST_PROJECT_STATUS_OPEN,
        )
        self.project.participants.add(self.owner)
        self.project.skills.add(self.skill1)

    def test_project_list_view(self):
        response = self.client.get(reverse("projects:project_list"))
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertTemplateUsed(response, "projects/project_list.html")
        self.assertContains(response, self.project.name)

    def test_project_list_filter_by_skill(self):
        response = self.client.get(
            reverse("projects:project_list") + f"?skill={TEST_SKILL_PYTHON}"
        )
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertContains(response, self.project.name)

        response = self.client.get(
            reverse("projects:project_list") + f"?skill={TEST_SKILL_REACT}"
        )
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertNotContains(response, self.project.name)

    def test_project_list_pagination(self):
        for i in range(PAGINATION_CREATE_COUNT):
            Project.objects.create(
                name=f"Project {i}",
                description="Test",
                owner=self.owner,
                status=TEST_PROJECT_STATUS_OPEN,
            )
        response = self.client.get(reverse("projects:project_list"))
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["page_obj"]), PAGINATION_COUNT)

    def test_project_detail_view(self):
        response = self.client.get(
            reverse("projects:project_detail", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertTemplateUsed(response, "projects/project-details.html")
        self.assertContains(response, self.project.name)
        self.assertContains(response, TEST_SKILL_PYTHON)

    def test_project_create_view_get(self):
        self.client.login(
            email=TEST_OWNER_EMAIL, password=TEST_OWNER_PASSWORD
        )
        response = self.client.get(reverse("projects:project_create"))
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertTemplateUsed(response, "projects/create-project.html")
        self.assertFalse(response.context["is_edit"])

    def test_project_create_view_post(self):
        self.client.login(
            email=TEST_OWNER_EMAIL, password=TEST_OWNER_PASSWORD
        )
        response = self.client.post(
            reverse("projects:project_create"),
            {
                "name": NEW_PROJECT_NAME,
                "description": NEW_PROJECT_DESCRIPTION,
                "status": TEST_PROJECT_STATUS_OPEN,
            },
        )
        project = Project.objects.get(name=NEW_PROJECT_NAME)
        self.assertRedirects(
            response,
            reverse("projects:project_detail", kwargs={"pk": project.pk}),
        )
        self.assertEqual(project.owner, self.owner)
        self.assertTrue(project.participants.filter(id=self.owner.id).exists())

    def test_project_create_not_authenticated(self):
        response = self.client.get(reverse("projects:project_create"))
        expected_url = (
            reverse("users:login")
            + "?next="
            + reverse("projects:project_create")
        )
        self.assertRedirects(response, expected_url)

    def test_project_edit_owner(self):
        self.client.login(
            email=TEST_OWNER_EMAIL, password=TEST_OWNER_PASSWORD
        )
        response = self.client.get(
            reverse("projects:project_edit", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertTrue(response.context["is_edit"])

        response = self.client.post(
            reverse("projects:project_edit", kwargs={"pk": self.project.pk}),
            {
                "name": UPDATED_PROJECT_NAME,
                "description": UPDATED_PROJECT_DESCRIPTION,
                "status": TEST_PROJECT_STATUS_OPEN,
            },
        )
        self.assertRedirects(
            response,
            reverse("projects:project_detail", kwargs={"pk": self.project.pk}),
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, UPDATED_PROJECT_NAME)

    def test_project_edit_not_owner(self):
        self.client.login(
            email=TEST_OTHER_EMAIL, password=TEST_OTHER_PASSWORD
        )
        response = self.client.get(
            reverse("projects:project_edit", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, HTTP_FOUND)


class SkillsAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            email=TEST_OWNER_EMAIL,
            name=TEST_OWNER_NAME,
            surname=TEST_OWNER_SURNAME,
            password=TEST_OWNER_PASSWORD,
        )
        self.other_user = User.objects.create_user(
            email=TEST_OTHER_EMAIL,
            name=TEST_OTHER_NAME,
            surname=TEST_USER_SURNAME,
            password=TEST_OTHER_PASSWORD,
        )
        self.project = Project.objects.create(
            name=TEST_PROJECT_NAME,
            description=TEST_PROJECT_DESCRIPTION,
            owner=self.owner,
            status=TEST_PROJECT_STATUS_OPEN,
        )
        self.skill = Skill.objects.create(name=TEST_SKILL_PYTHON)

    def test_skill_autocomplete(self):
        response = self.client.get(
            reverse("projects:skill_autocomplete") + "?q=Pyt"
        )
        self.assertEqual(response.status_code, HTTP_OK)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], TEST_SKILL_PYTHON)

    def test_skill_autocomplete_empty(self):
        response = self.client.get(
            reverse("projects:skill_autocomplete") + "?q="
        )
        self.assertEqual(response.status_code, HTTP_OK)
        data = json.loads(response.content)
        self.assertEqual(len(data), 0)

    def test_add_existing_skill(self):
        self.client.login(
            email=TEST_OWNER_EMAIL, password=TEST_OWNER_PASSWORD
        )
        response = self.client.post(
            reverse("projects:add_skill", kwargs={"pk": self.project.pk}),
            data=json.dumps({"skill_id": self.skill.id}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_OK)
        data = json.loads(response.content)
        self.assertTrue(data["added"])
        self.assertTrue(
            self.project.skills.filter(id=self.skill.id).exists()
        )

    def test_add_new_skill(self):
        self.client.login(
            email=TEST_OWNER_EMAIL, password=TEST_OWNER_PASSWORD
        )
        response = self.client.post(
            reverse("projects:add_skill", kwargs={"pk": self.project.pk}),
            data=json.dumps({"name": TEST_SKILL_DJANGO}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_OK)
        data = json.loads(response.content)
        self.assertTrue(data["added"])
        self.assertTrue(data["created"])
        self.assertTrue(Skill.objects.filter(name=TEST_SKILL_DJANGO).exists())

    def test_add_duplicate_skill(self):
        self.client.login(
            email=TEST_OWNER_EMAIL, password=TEST_OWNER_PASSWORD
        )
        self.project.skills.add(self.skill)
        response = self.client.post(
            reverse("projects:add_skill", kwargs={"pk": self.project.pk}),
            data=json.dumps({"skill_id": self.skill.id}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_OK)
        data = json.loads(response.content)
        self.assertFalse(data["added"])

    def test_add_skill_not_owner(self):
        self.client.login(
            email=TEST_OTHER_EMAIL, password=TEST_OTHER_PASSWORD
        )
        response = self.client.post(
            reverse("projects:add_skill", kwargs={"pk": self.project.pk}),
            data=json.dumps({"name": TEST_SKILL_DJANGO}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, HTTP_FORBIDDEN)

    def test_remove_skill(self):
        self.client.login(
            email=TEST_OWNER_EMAIL, password=TEST_OWNER_PASSWORD
        )
        self.project.skills.add(self.skill)
        response = self.client.post(
            reverse(
                "projects:remove_skill",
                kwargs={"pk": self.project.pk, "skill_pk": self.skill.pk},
            )
        )
        self.assertEqual(response.status_code, HTTP_OK)
        self.assertFalse(
            self.project.skills.filter(id=self.skill.id).exists()
        )
        self.assertTrue(Skill.objects.filter(id=self.skill.id).exists())


class ParticipationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            email=TEST_OWNER_EMAIL,
            name=TEST_OWNER_NAME,
            surname=TEST_OWNER_SURNAME,
            password=TEST_OWNER_PASSWORD,
        )
        self.user = User.objects.create_user(
            email=TEST_USER_EMAIL,
            name=TEST_USER_NAME,
            surname=TEST_USER_SURNAME,
            password=TEST_USER_PASSWORD,
        )
        self.project = Project.objects.create(
            name=TEST_PROJECT_NAME,
            description=TEST_PROJECT_DESCRIPTION,
            owner=self.owner,
            status=TEST_PROJECT_STATUS_OPEN,
        )
        self.project.participants.add(self.owner)

    def test_toggle_participate_join(self):
        self.client.login(
            email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD
        )
        response = self.client.post(
            reverse(
                "projects:toggle_participate",
                kwargs={"pk": self.project.pk},
            )
        )
        self.assertEqual(response.status_code, HTTP_OK)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["participant"])
        self.assertTrue(
            self.project.participants.filter(id=self.user.id).exists()
        )

    def test_toggle_participate_leave(self):
        self.client.login(
            email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD
        )
        self.project.participants.add(self.user)
        response = self.client.post(
            reverse(
                "projects:toggle_participate",
                kwargs={"pk": self.project.pk},
            )
        )
        self.assertEqual(response.status_code, HTTP_OK)
        data = json.loads(response.content)
        self.assertFalse(data["participant"])
        self.assertFalse(
            self.project.participants.filter(id=self.user.id).exists()
        )

    def test_complete_project(self):
        self.client.login(
            email=TEST_OWNER_EMAIL, password=TEST_OWNER_PASSWORD
        )
        response = self.client.post(
            reverse(
                "projects:complete_project",
                kwargs={"pk": self.project.pk},
            )
        )
        self.assertEqual(response.status_code, HTTP_OK)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "ok")
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, TEST_PROJECT_STATUS_CLOSED)

    def test_complete_project_not_owner(self):
        self.client.login(
            email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD
        )
        response = self.client.post(
            reverse(
                "projects:complete_project",
                kwargs={"pk": self.project.pk},
            )
        )
        self.assertEqual(response.status_code, HTTP_FORBIDDEN)