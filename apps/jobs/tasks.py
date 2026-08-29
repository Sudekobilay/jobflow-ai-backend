from celery import shared_task
from django.core.management import call_command
from apps.jobs.models import Job


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def sync_jobs_task(self, source="all", limit=100, deactivate_stale=False):
    call_command("sync_jobs", source=source, limit=limit, deactivate_stale=deactivate_stale)
    return {"source": source, "limit": limit, "status": "completed"}


@shared_task
def expire_jobs_task():
    from django.utils import timezone

    return Job.objects.filter(is_active=True, expires_at__isnull=False, expires_at__lte=timezone.now()).update(is_active=False)