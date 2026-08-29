from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import EmailDelivery


User = get_user_model()


class EmailAutomationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="email@example.com", password="StrongPass123")
        self.client.force_authenticate(user=self.user)

    def test_draft_requires_approval_before_sending(self):
        response = self.client.post(
            reverse("email-draft-list"),
            {"recipient_email": "company@example.com", "subject": "Application", "body": "Hello"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        draft_id = response.data["id"]

        blocked = self.client.post(reverse("email-draft-send", kwargs={"pk": draft_id}))
        self.assertEqual(blocked.status_code, status.HTTP_409_CONFLICT)

        approved = self.client.post(reverse("email-draft-approve", kwargs={"pk": draft_id}))
        self.assertEqual(approved.status_code, status.HTTP_200_OK)
        sent = self.client.post(reverse("email-draft-send", kwargs={"pk": draft_id}))
        self.assertEqual(sent.status_code, status.HTTP_200_OK)
        self.assertEqual(sent.data["status"], "sent")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(EmailDelivery.objects.count(), 1)

    def test_other_user_cannot_access_draft(self):
        response = self.client.post(
            reverse("email-draft-list"),
            {"recipient_email": "company@example.com", "subject": "Application", "body": "Hello"},
            format="json",
        )
        other_user = User.objects.create_user(email="other-email@example.com", password="StrongPass123")
        self.client.force_authenticate(user=other_user)
        detail = self.client.get(reverse("email-draft-detail", kwargs={"pk": response.data["id"]}))
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)
