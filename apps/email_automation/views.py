from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status, throttling
from rest_framework.response import Response
from rest_framework.views import APIView

from django.core.signing import BadSignature, SignatureExpired, TimestampSigner

from .models import EmailDelivery, EmailDraft, GmailAccount, GmailOAuthState
from .gmail import exchange_code, get_gmail_profile, revoke_token
from .services import send_approved_draft
from .serializers import EmailDeliverySerializer, EmailDraftSerializer


class EmailUserRateThrottle(throttling.UserRateThrottle):
	scope = "email"


class EmailDraftListView(generics.ListCreateAPIView):
	permission_classes = [permissions.IsAuthenticated]
	serializer_class = EmailDraftSerializer

	def get_queryset(self):
		return EmailDraft.objects.filter(user=self.request.user).order_by("-created_at")

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)


class EmailDraftDetailView(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = [permissions.IsAuthenticated]
	serializer_class = EmailDraftSerializer

	def get_queryset(self):
		return EmailDraft.objects.filter(user=self.request.user)


class EmailHistoryView(generics.ListAPIView):
	permission_classes = [permissions.IsAuthenticated]
	serializer_class = EmailDeliverySerializer

	def get_queryset(self):
		return EmailDelivery.objects.filter(draft__user=self.request.user).select_related("draft")


class EmailDraftApprovalView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def post(self, request, pk):
		draft = get_object_or_404(EmailDraft, pk=pk, user=request.user)
		if draft.status != "draft":
			return Response({"detail": "Yalnızca draft durumundaki email onaylanabilir."}, status=status.HTTP_409_CONFLICT)
		draft.status = "approved"
		draft.approved_at = timezone.now()
		draft.save(update_fields=["status", "approved_at", "updated_at"])
		return Response(EmailDraftSerializer(draft).data)


class EmailDraftSendView(APIView):
	permission_classes = [permissions.IsAuthenticated]
	throttle_classes = [EmailUserRateThrottle]

	def post(self, request, pk):
		draft = get_object_or_404(EmailDraft, pk=pk, user=request.user)
		if draft.status != "approved":
			return Response({"detail": "Email gönderilmeden önce kullanıcı onayı gerekir."}, status=status.HTTP_409_CONFLICT)
		attempt_count = getattr(draft, "_email_attempt_count", 1)
		limit = int(getattr(settings, "EMAIL_DAILY_LIMIT", 20))
		recent_count = EmailDelivery.objects.filter(draft__user=request.user, status="sent", delivered_at__date=timezone.localdate()).count()
		if recent_count >= limit:
			return Response({"detail": "Günlük email gönderim limitine ulaşıldı."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
		try:
			send_approved_draft(draft)
		except Exception as exc:
			draft.status = "failed"
			draft.last_error = str(exc)
			draft.save(update_fields=["status", "last_error", "updated_at"])
			EmailDelivery.objects.create(draft=draft, status="failed", error_message=str(exc), attempt_count=attempt_count, next_retry_at=timezone.now() + timedelta(minutes=15))
			return Response({"detail": "Email gönderilemedi."}, status=status.HTTP_502_BAD_GATEWAY)
		draft.status = "sent"
		draft.sent_at = timezone.now()
		draft.save(update_fields=["status", "sent_at", "updated_at"])
		EmailDelivery.objects.create(draft=draft, status="sent")
		return Response(EmailDraftSerializer(draft).data)


class EmailDraftRetryView(EmailDraftSendView):
	def post(self, request, pk):
		draft = get_object_or_404(EmailDraft, pk=pk, user=request.user)
		if draft.status != "failed":
			return Response({"detail": "Yalnızca başarısız email tekrar denenebilir."}, status=status.HTTP_409_CONFLICT)
		last_delivery = draft.deliveries.filter(status="failed").order_by("-delivered_at").first()
		if last_delivery is None:
			return Response({"detail": "Tekrar denenecek gönderim kaydı bulunamadı."}, status=status.HTTP_409_CONFLICT)
		if last_delivery.attempt_count >= settings.EMAIL_MAX_RETRIES:
			return Response({"detail": "Maksimum email deneme sayısına ulaşıldı."}, status=status.HTTP_409_CONFLICT)
		if last_delivery.next_retry_at and last_delivery.next_retry_at > timezone.now():
			return Response({"detail": "Email retry zamanı henüz gelmedi."}, status=status.HTTP_409_CONFLICT)
		draft.status = "approved"
		draft.save(update_fields=["status", "updated_at"])
		draft._email_attempt_count = last_delivery.attempt_count + 1
		return super().post(request, pk)


class GmailConnectView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		if not settings.GMAIL_CLIENT_ID:
			return Response({"detail": "Gmail OAuth yapılandırılmamış."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
		state = TimestampSigner().sign(str(request.user.pk))
		GmailOAuthState.objects.update_or_create(user=request.user, defaults={"state": state})
		params = {"client_id": settings.GMAIL_CLIENT_ID, "redirect_uri": settings.GMAIL_REDIRECT_URI, "response_type": "code", "access_type": "offline", "prompt": "consent", "state": state, "scope": "https://www.googleapis.com/auth/gmail.send"}
		return Response({"authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)})


class GmailCallbackView(APIView):
	permission_classes = [permissions.AllowAny]

	def _complete(self, request, code, state):
		if not settings.GMAIL_TOKEN_ENCRYPTION_KEY:
			return Response({"detail": "GMAIL_TOKEN_ENCRYPTION_KEY yapılandırılmamış."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
		try:
			user_id = TimestampSigner().unsign(state, max_age=600)
			oauth_state = GmailOAuthState.objects.get(user_id=user_id, state=state)
			tokens = exchange_code(code)
			if not tokens.get("refresh_token"):
				return Response({"detail": "Google refresh token döndürmedi."}, status=status.HTTP_400_BAD_REQUEST)
			profile = get_gmail_profile(tokens["access_token"])
			if not profile.get("emailAddress"):
				return Response({"detail": "Gmail hesabı doğrulanamadı."}, status=status.HTTP_401_UNAUTHORIZED)
			account = GmailAccount.objects.update_or_create(user_id=user_id, defaults={"email": profile["emailAddress"], "encrypted_refresh_token": ""})[0]
			account.set_refresh_token(tokens["refresh_token"])
			account.save(update_fields=["encrypted_refresh_token", "updated_at"])
			oauth_state.delete()
			return Response({"connected": True, "email": account.email})
		except (BadSignature, SignatureExpired, GmailOAuthState.DoesNotExist):
			return Response({"detail": "OAuth state geçersiz veya süresi dolmuş."}, status=status.HTTP_400_BAD_REQUEST)
		except Exception:
			return Response({"detail": "Gmail OAuth callback başarısız."}, status=status.HTTP_400_BAD_REQUEST)

	def get(self, request):
		return self._complete(request, request.query_params.get("code", ""), request.query_params.get("state", ""))

	def post(self, request):
		return self._complete(request, request.data.get("code", ""), request.data.get("state", ""))


class GmailDisconnectView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def post(self, request):
		account = get_object_or_404(GmailAccount, user=request.user)
		try:
			if settings.GMAIL_TOKEN_ENCRYPTION_KEY:
				revoke_token(account.get_refresh_token())
		except Exception:
			pass
		account.is_active = False
		account.revoked_at = timezone.now()
		account.save(update_fields=["is_active", "revoked_at", "updated_at"])
		return Response({"disconnected": True})

# Create your views here.
