from django.contrib.admin.sites import site
from django.test import SimpleTestCase

from apps.ai_services.models import AIUsage, AssistantConversation, AssistantMessage, JobMatch
from apps.applications.models import CV, CVAnalysis, CVVersion, JobApplication
from apps.email_automation.models import EmailDelivery, EmailDraft, GmailAccount
from apps.jobs.models import Job, JobSyncRun
from apps.notifications.models import Notification, NotificationPreference


class AdminRegistrationTests(SimpleTestCase):
    def test_product_models_are_registered(self):
        models = (
            AIUsage, AssistantConversation, AssistantMessage, JobMatch,
            CV, CVAnalysis, CVVersion, JobApplication, EmailDelivery,
            EmailDraft, GmailAccount, Job, JobSyncRun, Notification,
            NotificationPreference,
        )
        for model in models:
            self.assertIn(model, site._registry)