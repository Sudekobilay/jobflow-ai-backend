from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.jobs.models import Job


class Command(BaseCommand):
    help = "Deactivate expired jobs."

    def handle(self, *args, **options):
        count = Job.objects.filter(is_active=True, expires_at__isnull=False, expires_at__lte=timezone.now()).update(is_active=False)
        self.stdout.write(self.style.SUCCESS(f"Deactivated {count} expired jobs."))
