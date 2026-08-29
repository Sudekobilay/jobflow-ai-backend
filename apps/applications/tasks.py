from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.notifications.models import Notification

from .models import ApplicationReminder, Interview


@shared_task
def create_interview_reminders_task():
    now = timezone.now()
    upcoming = Interview.objects.select_related("application").filter(scheduled_at__gte=now, scheduled_at__lte=now + timedelta(hours=24))
    created = 0
    for interview in upcoming:
        _, was_created = Notification.objects.get_or_create(
            user=interview.application.user,
            type="interview",
            related_application=interview.application,
            title="Yaklaşan mülakat",
            dedupe_key=f"interview:{interview.pk}",
            defaults={"message": f"Mülakatınız {interview.scheduled_at.isoformat()} tarihinde."},
        )
        created += int(was_created)
    return created


@shared_task
def create_application_reminders_task():
    now = timezone.now()
    due = ApplicationReminder.objects.select_related("application").filter(is_completed=False, remind_at__lte=now)
    created = 0
    for reminder in due:
        _, was_created = Notification.objects.get_or_create(
            user=reminder.application.user,
            type="application",
            related_application=reminder.application,
            title="Başvuru hatırlatması",
            dedupe_key=f"application-reminder:{reminder.pk}",
            defaults={"message": reminder.message},
        )
        reminder.is_completed = True
        reminder.save(update_fields=["is_completed"])
        created += int(was_created)
    return created