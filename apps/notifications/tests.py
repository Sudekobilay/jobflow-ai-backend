from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Notification
from apps.applications.models import ApplicationReminder, Interview
from apps.applications.tasks import create_application_reminders_task, create_interview_reminders_task
from apps.jobs.models import Job
from apps.applications.models import CV, JobApplication
from django.utils import timezone
from datetime import timedelta


User = get_user_model()


class NotificationEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="notifications@example.com", password="StrongPass123")
        other_user = User.objects.create_user(email="other-notifications@example.com", password="StrongPass123")
        self.client.force_authenticate(user=self.user)
        Notification.objects.create(user=self.user, title="Interview", message="Tomorrow", type="interview")
        Notification.objects.create(user=other_user, title="Private", message="Hidden")

    def test_notifications_are_user_scoped_and_can_be_marked_read(self):
        response = self.client.get(reverse("notification-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        notification_id = response.data[0]["id"]
        read_response = self.client.patch(reverse("notification-read", kwargs={"pk": notification_id}))
        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        self.assertTrue(read_response.data["is_read"])

    def test_preferences_are_created_and_updated(self):
        response = self.client.get(reverse("notification-preferences"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["email_enabled"])

        response = self.client.patch(
            reverse("notification-preferences"),
            {"email_enabled": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["email_enabled"])

    def test_due_application_reminder_creates_notification(self):
        cv = self.user.cvs.create(title="CV", summary="Backend")
        job = Job.objects.create(title="Backend", company="Acme", description="API")
        application = JobApplication.objects.create(user=self.user, cv=cv, job=job)
        reminder = ApplicationReminder.objects.create(
            application=application,
            remind_at=timezone.now() - timedelta(minutes=1),
            message="Follow up",
        )

        created = create_application_reminders_task()

        self.assertEqual(created, 1)
        self.assertTrue(reminder.__class__.objects.get(pk=reminder.pk).is_completed)
        self.assertEqual(Notification.objects.filter(user=self.user, type="application").count(), 1)

    def test_upcoming_interview_creates_notification(self):
        cv = self.user.cvs.create(title="CV", summary="Backend")
        job = Job.objects.create(title="Backend", company="Acme", description="API")
        application = JobApplication.objects.create(user=self.user, cv=cv, job=job)
        Interview.objects.create(application=application, scheduled_at=timezone.now() + timedelta(hours=2))

        self.assertEqual(create_interview_reminders_task(), 1)
        self.assertEqual(Notification.objects.filter(user=self.user, type="interview", title="Yaklaşan mülakat").count(), 1)
