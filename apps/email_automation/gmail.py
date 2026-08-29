import base64
import json
from email.message import EmailMessage
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from django.conf import settings


def exchange_code(code):
    payload = urlencode({"code": code, "client_id": settings.GMAIL_CLIENT_ID, "client_secret": settings.GMAIL_CLIENT_SECRET, "redirect_uri": settings.GMAIL_REDIRECT_URI, "grant_type": "authorization_code"}).encode()
    request = Request("https://oauth2.googleapis.com/token", data=payload, method="POST")
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode())


def refresh_access_token(refresh_token):
    payload = urlencode({"refresh_token": refresh_token, "client_id": settings.GMAIL_CLIENT_ID, "client_secret": settings.GMAIL_CLIENT_SECRET, "grant_type": "refresh_token"}).encode()
    request = Request("https://oauth2.googleapis.com/token", data=payload, method="POST")
    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode())["access_token"]
    except HTTPError as exc:
        if exc.code == 400:
            raise GmailTokenRevokedError from exc
        raise


class GmailTokenRevokedError(Exception):
    pass


def revoke_token(refresh_token):
    request = Request(
        "https://oauth2.googleapis.com/revoke",
        data=urlencode({"token": refresh_token}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        return response.status


def get_gmail_profile(access_token):
    request = Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/profile",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode())


def send_gmail(account, draft):
    message = EmailMessage()
    message["To"] = draft.recipient_email
    message["Subject"] = draft.subject
    message.set_content(draft.body)
    if draft.cv and draft.cv.file:
        message.add_attachment(draft.cv.file.read(), maintype="application", subtype="octet-stream", filename=draft.cv.file.name.split("/")[-1])
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode().rstrip("=")
    request = Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        data=json.dumps({"raw": raw}).encode(),
        headers={"Authorization": f"Bearer {refresh_access_token(account.get_refresh_token())}", "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=15) as response:
        return response.status