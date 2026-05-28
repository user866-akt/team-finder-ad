import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Project, Skill

User = get_user_model()


class ProjectModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            name="Owner",
            surname="User",
            password="testpass123",
        )
        self.skill = Skill.objects.create(name="Python")

    def test_create_skill(self):
        skill = Skill.objects.create(name="Django")
        self.assertEqual(skill.name, "Django")
        self.assertEqual(str(skill), "Django")

    def test_skill_unique(self):
        with self.assertRaises(Exception):
            Skill.objects.create(name="Python")

    def test_create_project(self):
        project = Project.objects.create(
            name="Test Project",
            description="Test description",
            owner=self.user,
            status="open",
        )
        project.participants.add(self.user)
        project.skills.add(self.skill)

        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.owner, self.user)
        self.assertEqual(project.status, "open")
        self.assertTrue(project.is_open)
        self.assertEqual(project.participants.count(), 1)
        self.assertEqual(project.skills.count(), 1)
        self.assertEqual(str(project), "Test Project")

    def test_project_status_closed(self):
        project = Project.objects.create(
            name="Closed Project", description="Test", owner=self.user, status="closed"
        )
        self.assertFalse(project.is_open)


class ProjectViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            email="owner@example.com",
            name="Owner",
            surname="User",
            password="ownerpass123",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            name="Other",
            surname="User",
            password="otherpass123",
        )
        self.skill1 = Skill.objects.create(name="Python")
        self.skill2 = Skill.objects.create(name="Django")

        self.project = Project.objects.create(
            name="Test Project",
            description="Test description",
            owner=self.owner,
            status="open",
        )
        self.project.participants.add(self.owner)
        self.project.skills.add(self.skill1)

    def test_project_list_view(self):
        response = self.client.get(reverse("projects:project_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projects/project_list.html")
        self.assertContains(response, self.project.name)

    def test_project_list_filter_by_skill(self):
        response = self.client.get(reverse("projects:project_list") + "?skill=Python")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project.name)

        response = self.client.get(reverse("projects:project_list") + "?skill=React")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.project.name)

    def test_project_list_pagination(self):
        for i in range(13):
            Project.objects.create(
                name=f"Project {i}", description="Test", owner=self.owner, status="open"
            )
        response = self.client.get(reverse("projects:project_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["page_obj"]), 12)

    def test_project_detail_view(self):
        response = self.client.get(
            reverse("projects:project_detail", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projects/project-details.html")
        self.assertContains(response, self.project.name)
        self.assertContains(response, "Python")

    def test_project_create_view_get(self):
        self.client.login(email="owner@example.com", password="ownerpass123")
        response = self.client.get(reverse("projects:project_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projects/create-project.html")
        self.assertFalse(response.context["is_edit"])

    def test_project_create_view_post(self):
        self.client.login(email="owner@example.com", password="ownerpass123")
        response = self.client.post(
            reverse("projects:project_create"),
            {
                "name": "New Project",
                "description": "New description",
                "status": "open",
            },
        )
        project = Project.objects.get(name="New Project")
        self.assertRedirects(
            response, reverse("projects:project_detail", kwargs={"pk": project.pk})
        )
        self.assertEqual(project.owner, self.owner)
        self.assertTrue(project.participants.filter(id=self.owner.id).exists())

    def test_project_create_not_authenticated(self):
        response = self.client.get(reverse("projects:project_create"))
        self.assertRedirects(
            response,
            reverse("users:login") + "?next=" + reverse("projects:project_create"),
        )

    def test_project_edit_owner(self):
        self.client.login(email="owner@example.com", password="ownerpass123")

        response = self.client.get(
            reverse("projects:project_edit", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_edit"])

        response = self.client.post(
            reverse("projects:project_edit", kwargs={"pk": self.project.pk}),
            {
                "name": "Updated Project",
                "description": "Updated description",
                "status": "open",
            },
        )
        self.assertRedirects(
            response, reverse("projects:project_detail", kwargs={"pk": self.project.pk})
        )

        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Updated Project")

    def test_project_edit_not_owner(self):
        self.client.login(email="other@example.com", password="otherpass123")

        response = self.client.get(
            reverse("projects:project_edit", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 302)


class SkillsAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            email="owner@example.com",
            name="Owner",
            surname="User",
            password="ownerpass123",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            name="Other",
            surname="User",
            password="otherpass123",
        )
        self.project = Project.objects.create(
            name="Test Project", description="Test", owner=self.owner, status="open"
        )
        self.skill = Skill.objects.create(name="Python")

    def test_skill_autocomplete(self):
        response = self.client.get(reverse("projects:skill_autocomplete") + "?q=Pyt")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Python")

    def test_skill_autocomplete_empty(self):
        response = self.client.get(reverse("projects:skill_autocomplete") + "?q=")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 0)

    def test_add_existing_skill(self):
        self.client.login(email="owner@example.com", password="ownerpass123")

        response = self.client.post(
            reverse("projects:add_skill", kwargs={"pk": self.project.pk}),
            data=json.dumps({"skill_id": self.skill.id}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["added"])
        self.assertTrue(self.project.skills.filter(id=self.skill.id).exists())

    def test_add_new_skill(self):
        self.client.login(email="owner@example.com", password="ownerpass123")

        response = self.client.post(
            reverse("projects:add_skill", kwargs={"pk": self.project.pk}),
            data=json.dumps({"name": "Django"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["added"])
        self.assertTrue(data["created"])
        self.assertTrue(Skill.objects.filter(name="Django").exists())

    def test_add_duplicate_skill(self):
        self.client.login(email="owner@example.com", password="ownerpass123")
        self.project.skills.add(self.skill)

        response = self.client.post(
            reverse("projects:add_skill", kwargs={"pk": self.project.pk}),
            data=json.dumps({"skill_id": self.skill.id}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data["added"])

    def test_add_skill_not_owner(self):
        self.client.login(email="other@example.com", password="otherpass123")

        response = self.client.post(
            reverse("projects:add_skill", kwargs={"pk": self.project.pk}),
            data=json.dumps({"name": "Django"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_remove_skill(self):
        self.client.login(email="owner@example.com", password="ownerpass123")
        self.project.skills.add(self.skill)

        response = self.client.post(
            reverse(
                "projects:remove_skill",
                kwargs={"pk": self.project.pk, "skill_pk": self.skill.pk},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.project.skills.filter(id=self.skill.id).exists())
        self.assertTrue(Skill.objects.filter(id=self.skill.id).exists())


class ParticipationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            email="owner@example.com",
            name="Owner",
            surname="User",
            password="ownerpass123",
        )
        self.user = User.objects.create_user(
            email="user@example.com",
            name="User",
            surname="Test",
            password="userpass123",
        )
        self.project = Project.objects.create(
            name="Test Project", description="Test", owner=self.owner, status="open"
        )
        self.project.participants.add(self.owner)

    def test_toggle_participate_join(self):
        self.client.login(email="user@example.com", password="userpass123")

        response = self.client.post(
            reverse("projects:toggle_participate", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["participant"])
        self.assertTrue(self.project.participants.filter(id=self.user.id).exists())

    def test_toggle_participate_leave(self):
        self.client.login(email="user@example.com", password="userpass123")
        self.project.participants.add(self.user)

        response = self.client.post(
            reverse("projects:toggle_participate", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data["participant"])
        self.assertFalse(self.project.participants.filter(id=self.user.id).exists())

    def test_complete_project(self):
        self.client.login(email="owner@example.com", password="ownerpass123")

        response = self.client.post(
            reverse("projects:complete_project", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "ok")

        self.project.refresh_from_db()
        self.assertEqual(self.project.status, "closed")

    def test_complete_project_not_owner(self):
        self.client.login(email="user@example.com", password="userpass123")

        response = self.client.post(
            reverse("projects:complete_project", kwargs={"pk": self.project.pk})
        )
        self.assertEqual(response.status_code, 403)
