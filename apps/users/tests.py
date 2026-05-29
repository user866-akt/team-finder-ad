from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

TEST_EMAIL = "test@example.com"
TEST_NAME = "Test"
TEST_SURNAME = "User"
TEST_PASSWORD = "testpass123"

ADMIN_EMAIL = "admin@example.com"
ADMIN_NAME = "Admin"
ADMIN_SURNAME = "Adminov"
ADMIN_PASSWORD = "adminpass123"

USER_EMAIL = "user@example.com"
USER_PASSWORD = "testpass123"
OTHER_USER_EMAIL = "other@example.com"
OTHER_USER_PASSWORD = "otherpass123"

NEW_USER_EMAIL = "new@example.com"
NEW_USER_PASSWORD = "newpass123"
INVALID_EMAIL = "invalid-email"

OLD_PASSWORD = "oldpass123"
NEW_PASSWORD = "newpass456"
WRONG_PASSWORD = "wrongpass"

VALID_PHONE = "+79001234567"
INVALID_PHONE = "12345"
VALID_GITHUB_URL = "https://github.com/test"

PHONE_ERROR_MESSAGE = (
    "Номер телефона должен быть в формате +7XXXXXXXXXX или 8XXXXXXXXXX"
    " (11 цифр после префикса)."
)


class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            "email": TEST_EMAIL,
            "name": TEST_NAME,
            "surname": TEST_SURNAME,
            "password": TEST_PASSWORD,
        }

    def test_create_user(self):
        user = User.objects.create_user(**self.user_data)

        self.assertEqual(user.email, TEST_EMAIL)
        self.assertEqual(user.name, TEST_NAME)
        self.assertEqual(user.surname, TEST_SURNAME)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password(TEST_PASSWORD))
        self.assertTrue(user.avatar)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email=ADMIN_EMAIL,
            name=ADMIN_NAME,
            surname=ADMIN_SURNAME,
            password=ADMIN_PASSWORD,
        )

        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)

    def test_user_str(self):
        user = User.objects.create_user(**self.user_data)
        expected = f"{TEST_NAME} {TEST_SURNAME} ({TEST_EMAIL})"
        self.assertEqual(str(user), expected)

    def test_email_unique(self):
        User.objects.create_user(**self.user_data)

        with self.assertRaises(Exception):
            User.objects.create_user(
                email=TEST_EMAIL,
                name="Another",
                surname="User",
                password="pass123",
            )

    def test_get_full_name(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), f"{TEST_NAME} {TEST_SURNAME}")

    def test_avatar_generation(self):
        user = User.objects.create_user(**self.user_data)
        self.assertIsNotNone(user.avatar)
        self.assertTrue(user.avatar.name.startswith("avatars/avatar_"))


class UserViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email=USER_EMAIL,
            name=TEST_NAME,
            surname=TEST_SURNAME,
            password=USER_PASSWORD,
        )
        self.other_user = User.objects.create_user(
            email=OTHER_USER_EMAIL,
            name="Other",
            surname="User",
            password=OTHER_USER_PASSWORD,
        )

    def test_register_view_get(self):
        response = self.client.get(reverse("users:register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")

    def test_register_view_post_success(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "email": NEW_USER_EMAIL,
                "name": "New",
                "surname": "User",
                "password": NEW_USER_PASSWORD,
            },
        )
        self.assertRedirects(response, reverse("projects:project_list"))
        self.assertTrue(User.objects.filter(email=NEW_USER_EMAIL).exists())

    def test_register_view_post_invalid(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "email": INVALID_EMAIL,
                "name": "",
                "surname": "",
                "password": "123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email=INVALID_EMAIL).exists())

    def test_login_view_get(self):
        response = self.client.get(reverse("users:login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/login.html")

    def test_login_view_post_success(self):
        response = self.client.post(
            reverse("users:login"),
            {
                "email": USER_EMAIL,
                "password": USER_PASSWORD,
            },
        )
        self.assertRedirects(response, reverse("projects:project_list"))

    def test_login_view_post_invalid(self):
        response = self.client.post(
            reverse("users:login"),
            {
                "email": USER_EMAIL,
                "password": WRONG_PASSWORD,
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_logout_view(self):
        self.client.login(email=USER_EMAIL, password=USER_PASSWORD)
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
        self.client.login(email=USER_EMAIL, password=USER_PASSWORD)

        response = self.client.get(
            reverse("users:user_edit", kwargs={"pk": self.user.pk})
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("users:user_edit", kwargs={"pk": self.user.pk}),
            {
                "name": "Updated",
                "surname": "Name",
                "phone": VALID_PHONE,
                "github_url": VALID_GITHUB_URL,
                "about": "About me",
            },
        )
        self.assertRedirects(
            response, reverse("users:user_detail", kwargs={"pk": self.user.pk})
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "Updated")

    def test_user_edit_view_not_owner(self):
        self.client.login(email=USER_EMAIL, password=USER_PASSWORD)
        response = self.client.get(
            reverse("users:user_edit", kwargs={"pk": self.other_user.pk})
        )
        self.assertEqual(response.status_code, 302)

    def test_user_edit_phone_validation(self):
        self.client.login(email=USER_EMAIL, password=USER_PASSWORD)
        response = self.client.post(
            reverse("users:user_edit", kwargs={"pk": self.user.pk}),
            {
                "name": TEST_NAME,
                "surname": TEST_SURNAME,
                "phone": INVALID_PHONE,
            },
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.errors)
        self.assertIn("phone", form.errors)
        self.assertIn(PHONE_ERROR_MESSAGE, form.errors["phone"])

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
            email=USER_EMAIL,
            name=TEST_NAME,
            surname=TEST_SURNAME,
            password=OLD_PASSWORD,
        )

    def test_password_change_success(self):
        self.client.login(email=USER_EMAIL, password=OLD_PASSWORD)

        response = self.client.post(
            reverse("users:change_password", kwargs={"pk": self.user.pk}),
            {
                "old_password": OLD_PASSWORD,
                "new_password1": NEW_PASSWORD,
                "new_password2": NEW_PASSWORD,
            },
        )
        self.assertRedirects(
            response, reverse("users:user_detail", kwargs={"pk": self.user.pk})
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))

    def test_password_change_wrong_old(self):
        self.client.login(email=USER_EMAIL, password=OLD_PASSWORD)

        response = self.client.post(
            reverse("users:change_password", kwargs={"pk": self.user.pk}),
            {
                "old_password": WRONG_PASSWORD,
                "new_password1": NEW_PASSWORD,
                "new_password2": NEW_PASSWORD,
            },
        )
        self.assertEqual(response.status_code, 200)