from django.core.management.base import BaseCommand, CommandError
from datetime import timedelta

from django.utils import timezone

from apps.jobs.integrations.adzuna import fetch_jobs as fetch_adzuna_jobs
from apps.jobs.integrations.arbeitnow import fetch_jobs as fetch_arbeitnow_jobs
from apps.jobs.integrations.jooble import fetch_jobs as fetch_jooble_jobs
from apps.jobs.integrations.remoteok import fetch_jobs
from apps.jobs.models import Job, JobSyncRun


class Command(BaseCommand):
    help = "Synchronize permitted public job feeds into the JobFlow catalog."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument(
            "--source",
            choices=("remoteok", "arbeitnow", "adzuna", "jooble", "all"),
            default="remoteok",
        )
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--deactivate-stale", action="store_true")

    def handle(self, *args, **options):
        limit = options["limit"]
        if limit < 1:
            raise CommandError("--limit must be greater than zero")

        sources = (options["source"],) if options["source"] != "all" else ("remoteok", "arbeitnow", "adzuna", "jooble")
        fetchers = {
            "remoteok": fetch_jobs,
            "arbeitnow": fetch_arbeitnow_jobs,
            "adzuna": fetch_adzuna_jobs,
            "jooble": fetch_jooble_jobs,
        }
        fetched_jobs = {}
        for source in sources:
            sync_run = JobSyncRun.objects.create(source=source)
            try:
                fetched_jobs[source] = fetchers[source](limit=limit)
            except Exception as exc:
                sync_run.status = "failed"
                sync_run.error_message = str(exc)
                sync_run.finished_at = timezone.now()
                sync_run.save(update_fields=["status", "error_message", "finished_at"])
                raise CommandError(f"{source} synchronization failed: {exc}") from exc
            sync_run.fetched_count = len(fetched_jobs[source])
            sync_run.save(update_fields=["fetched_count"])

        if options["dry_run"]:
            for source, jobs in fetched_jobs.items():
                sync_run = JobSyncRun.objects.filter(source=source, status="running").latest("started_at")
                sync_run.status = "success"
                sync_run.fetched_count = len(jobs)
                sync_run.finished_at = timezone.now()
                sync_run.save(update_fields=["status", "fetched_count", "finished_at"])
                self.stdout.write(self.style.SUCCESS(f"Fetched {len(jobs)} {source} jobs (dry run)."))
            return

        synced_at = timezone.now()
        for source, jobs in fetched_jobs.items():
            sync_run = JobSyncRun.objects.filter(source=source, status="running").latest("started_at")
            created_count = 0
            updated_count = 0
            seen_external_ids = set()
            for job_data in jobs:
                external_id = job_data["external_id"]
                seen_external_ids.add(external_id)
                job = Job.objects.filter(source=source, external_id=external_id).first()
                created = job is None
                if created:
                    job = Job(source=source, external_id=external_id)
                for field, value in {**job_data, "synced_at": synced_at, "user": None}.items():
                    setattr(job, field, value)
                if not job.expires_at:
                    job.expires_at = synced_at + timedelta(days=30)
                job.is_active = job.expires_at > synced_at
                job.save()
                if created:
                    created_count += 1
                else:
                    updated_count += 1

            if options["deactivate_stale"] and seen_external_ids:
                Job.objects.filter(source=source, is_active=True).exclude(external_id__in=seen_external_ids).update(is_active=False)

            self.stdout.write(
                self.style.SUCCESS(
                    f"{source} synchronization complete: {created_count} created, {updated_count} updated."
                )
            )
            sync_run.status = "success"
            sync_run.created_count = created_count
            sync_run.updated_count = updated_count
            sync_run.finished_at = timezone.now()
            sync_run.save(update_fields=["status", "created_count", "updated_count", "finished_at"])
