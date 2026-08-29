from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import EmailDelivery, EmailDraft
from .services import send_approved_draft


@shared_task
def retry_failed_emails_task():
    retried = 0
    delivery_ids = EmailDelivery.objects.filter(
        status="failed", next_retry_at__lte=timezone.now(), attempt_count__lt=settings.EMAIL_MAX_RETRIES
    ).values_list("id", flat=True)
    for delivery_id in delivery_ids:
        with transaction.atomic():
            delivery = EmailDelivery.objects.select_for_update().select_related("draft").filter(
                pk=delivery_id, status="failed", next_retry_at__lte=timezone.now(),
                attempt_count__lt=settings.EMAIL_MAX_RETRIES,
            ).first()
            if delivery is None or delivery.draft.status != "failed":
                continue
            draft = delivery.draft
            try:
                send_approved_draft(draft)
                draft.status = "sent"
                draft.sent_at = timezone.now()
                draft.save(update_fields=["status", "sent_at", "updated_at"])
                EmailDelivery.objects.create(draft=draft, status="sent", attempt_count=delivery.attempt_count + 1)
            except Exception as exc:
                delivery.attempt_count += 1
                delivery.error_message = str(exc)
                delivery.next_retry_at = timezone.now() + timedelta(minutes=15)
                delivery.save(update_fields=["attempt_count", "error_message", "next_retry_at"])
            retried += 1
    return retried