from django.conf import settings
from django.core.mail import EmailMessage

from .gmail import GmailTokenRevokedError, send_gmail
from .models import EmailDraft, GmailAccount


def send_approved_draft(draft):
    account = GmailAccount.objects.filter(user=draft.user, is_active=True).first()
    if account and settings.GMAIL_TOKEN_ENCRYPTION_KEY:
        try:
            return send_gmail(account, draft)
        except GmailTokenRevokedError:
            account.is_active = False
            account.last_error = "Gmail refresh token geçersiz veya iptal edilmiş."
            account.save(update_fields=["is_active", "last_error", "updated_at"])
            raise
    message = EmailMessage(draft.subject, draft.body, settings.DEFAULT_FROM_EMAIL, [draft.recipient_email])
    if draft.cv and draft.cv.file:
        message.attach_file(draft.cv.file.path)
    return message.send(fail_silently=False)
