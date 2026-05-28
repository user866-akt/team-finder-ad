from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "test@example.com",
            "name": "Test",
            "surname": "User",
            "password": "testpass123",
        }

    def test_create_user(self):
        user = User.objects.create_user(**self.user_data)

        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.name, "Test")
        self.assertEqual(user.surname, "User")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password("testpass123"))
        self.assertTrue(user.avatar)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email="admin@example.com",
            name="Admin",
            surname="Adminov",
            password="adminpass123",
        )

        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)

    def test_user_str(self):
        user = User.objects.create_user(**self.user_data)
        expected = f"{user.name} {user.surname} ({user.email})"
        self.assertEqual(str(user), expected)

    def test_email_unique(self):
        User.objects.create_user(**self.user_data)

        with self.assertRaises(Exception):
            User.objects.create_user(
                email="test@example.com",
                name="Another",
                surname="User",
                password="pass123",
            )

    def test_get_full_name(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), "Test User")

    def test_avatar_generation(self):
        user = User.objects.create_user(**self.user_data)
        self.assertIsNotNone(user.avatar)
        self.assertTrue(user.avatar.name.startswith("avatars/avatar_"))


class UserViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="user@example.com",
            name="Test",
            surname="User",
            password="testpass123",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            name="Other",
            surname="User",
            password="otherpass123",
        )

    def test_register_view_get(self):
        response = self.client.get(reverse("users:register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")

    def test_register_view_post_success(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "email": "new@example.com",
                "name": "New",
                "surname": "User",
                "password": "newpass123",
            },
        )
        self.assertRedirects(response, reverse("projects:project_list"))
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

    def test_register_view_post_invalid(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "email": "invalid-email",
                "name": "",
                "surname": "",
                "password": "123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="invalid-email").exists())

    def test_login_view_get(self):
        response = self.client.get(reverse("users:login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/login.html")

    def test_login_view_post_success(self):
        response = self.client.post(
            reverse("users:login"),
            {
                "email": "user@example.com",
                "password": "testpass123",
            },
        )
        self.assertRedirects(response, reverse("projects:project_list"))

    def test_login_view_post_invalid(self):
        response = self.client.post(
            reverse("users:login"),
            {
                "email": "user@example.com",
                "password": "wrongpass",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_logout_view(self):
        self.client.login(email="user@example.com", password="testpass123")
        response = self.client.get(reverse("users:logout"))
        self.assertRedirects(response, reverse("projects:project_list"))

    def test_user_detail_view(self):
        response = self.client.get(
            reverse("users:user_detail", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/user-details.html")
        self.assertContains(response, self.user.name)

    def test_user_edit_view_owner(self):
        self.client.login(email="user@example.com", password="testpass123")

        response = self.client.get(
            reverse("users:user_edit", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("users:user_edit", kwargs={"pk": self.user.pk}),
            {
                "name": "Updated",
                "surname": "Name",
                "phone": "+79001234567",
                "github_url": "https://github.com/test",
                "about": "About me",
            },
        )
        self.assertRedirects(
            response, reverse("users:user_detail", kwargs={"pk": self.user.pk})
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "Updated")

    def test_user_edit_view_not_owner(self):
        self.client.login(email="user@example.com", password="testpass123")

        response = self.client.get(
            reverse("users:user_edit", kwargs={"pk": self.other_user.pk})
        )
        self.assertEqual(response.status_code, 302)

    def test_user_edit_phone_validation(self):
        self.client.login(email="user@example.com", password="testpass123")
        response = self.client.post(
            reverse("users:user_edit", kwargs={"pk": self.user.pk}),
            {
                "name": "Test",
                "surname": "User",
                "phone": "12345",
            },
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.errors)
        self.assertIn("phone", form.errors)
        self.assertIn(
            "Номер телефона должен быть в формате +7XXXXXXXXXX или 8XXXXXXXXXX (11 цифр после префикса).",
            form.errors["phone"],
        )

    def test_user_list_view(self):
        response = self.client.get(reverse("users:user_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/participants.html")
        self.assertContains(response, self.user.name)
        self.assertContains(response, self.other_user.name)


class PasswordChangeTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="user@example.com", name="Test", surname="User", password="oldpass123"
        )

    def test_password_change_success(self):
        self.client.login(email="user@example.com", password="oldpass123")

        response = self.client.post(
            reverse("users:change_password", kwargs={"pk": self.user.pk}),
            {
                "old_password": "oldpass123",
                "new_password1": "newpass456",
                "new_password2": "newpass456",
            },
        )
        self.assertRedirects(
            response, reverse("users:user_detail", kwargs={"pk": self.user.pk})
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass456"))

    def test_password_change_wrong_old(self):
        self.client.login(email="user@example.com", password="oldpass123")

        response = self.client.post(
            reverse("users:change_password", kwargs={"pk": self.user.pk}),
            {
                "old_password": "wrongpass",
                "new_password1": "newpass456",
                "new_password2": "newpass456",
            },
        )
        self.assertEqual(response.status_code, 200)
