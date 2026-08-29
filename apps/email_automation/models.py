from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models


class EmailDraft(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("approved", "Approved"),
        ("sent", "Sent"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_drafts",
    )
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    cv = models.ForeignKey(
        "applications.CV",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_drafts",
    )
    application = models.ForeignKey(
        "applications.JobApplication",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_drafts",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class GmailAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gmail_account")
    email = models.EmailField()
    encrypted_refresh_token = models.TextField()
    is_active = models.BooleanField(default=True)
    last_error = models.TextField(blank=True, default="")
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_refresh_token(self, token):
        self.encrypted_refresh_token = Fernet(settings.GMAIL_TOKEN_ENCRYPTION_KEY).encrypt(token.encode()).decode()

    def get_refresh_token(self):
        return Fernet(settings.GMAIL_TOKEN_ENCRYPTION_KEY).decrypt(self.encrypted_refresh_token.encode()).decode()


class GmailOAuthState(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gmail_oauth_state")
    state = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


class EmailDelivery(models.Model):
    STATUS_CHOICES = [
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    draft = models.ForeignKey(
        EmailDraft,
        on_delete=models.CASCADE,
        related_name="deliveries",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True, default="")
    attempt_count = models.PositiveSmallIntegerField(default=1)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(auto_now_add=True)
