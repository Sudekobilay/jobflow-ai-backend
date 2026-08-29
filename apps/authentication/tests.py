from django.core import mail
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase, override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse
from rest_framework.test import APITestCase

User = get_user_model()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetTests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(email="reset@example.com", password="OldPass123!")

	def test_password_reset_request_sends_email(self):
		response = self.client.post(reverse("password-reset"), {"email": self.user.email}, format="json")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(mail.outbox), 1)

	def test_password_reset_confirm_changes_password(self):
		uid = urlsafe_base64_encode(force_bytes(self.user.pk))
		token = default_token_generator.make_token(self.user)

		response = self.client.post(
			reverse("password-reset-confirm"),
			{"uid": uid, "token": token, "password": "NewPass123!"},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password("NewPass123!"))
