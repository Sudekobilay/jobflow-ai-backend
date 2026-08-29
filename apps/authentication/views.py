from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
import json
import os
from urllib.parse import urlencode
from urllib.request import urlopen
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.utils import extend_schema
from .serializers import GoogleLoginSerializer, LoginSerializer, RegisterSerializer, UserSerializer

User = get_user_model()


class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get("email", "").strip()
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            send_mail(
                "JobFlow AI password reset",
                f"Use uid={uid} and token={token} to reset your password.",
                None,
                [user.email],
                fail_silently=False,
            )
        return Response(
            {"detail": "If the account exists, a password reset email has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        uid = request.data.get("uid", "")
        token = request.data.get("token", "")
        password = request.data.get("password", "")
        if not uid or not token or len(password) < 8:
            return Response(
                {"detail": "uid, token and a password of at least 8 characters are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(uid)))
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is None or not default_token_generator.check_token(user, token):
            return Response({"detail": "Invalid or expired reset token."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(password)
        user.save(update_fields=["password"])
        return Response({"detail": "Password has been reset."}, status=status.HTTP_200_OK)

@extend_schema(
    summary="Kullanıcı kaydı",
    description="Yeni kullanıcı oluşturur. Email ve şifre ile kayıt yapılır.",
    tags=["Auth"],
)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

@extend_schema(
    summary="Giriş yap",
    description="E-posta ve şifre ile kullanıcı girişi yapar ve JWT token döner.",
    tags=["Auth"],
)

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

@extend_schema(
    summary="Me bilgisi",
    description="Giriş yapmış kullanıcının profil bilgilerini döner.",
    tags=["Auth"],
)

class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class GoogleTokenLoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = GoogleLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        token_key = "id_token" if data.get("id_token") else "access_token"
        endpoint = "https://oauth2.googleapis.com/tokeninfo"
        try:
            query = urlencode({token_key: data[token_key]})
            with urlopen(f"{endpoint}?{query}", timeout=5) as response:
                profile = json.loads(response.read().decode("utf-8"))
        except Exception:
            return Response({"detail": "Google token doğrulanamadı."}, status=status.HTTP_401_UNAUTHORIZED)
        expected_client_id = os.getenv("GOOGLE_CLIENT_ID")
        if token_key == "id_token" and expected_client_id and profile.get("aud") != expected_client_id:
            return Response({"detail": "Google token audience geçersiz."}, status=status.HTTP_401_UNAUTHORIZED)
        email = profile.get("email")
        google_sub = profile.get("sub")
        if not email or not google_sub or profile.get("email_verified") == "false":
            return Response({"detail": "Google hesabı doğrulanamadı."}, status=status.HTTP_401_UNAUTHORIZED)
        user = User.objects.filter(google_sub=google_sub).first() or User.objects.filter(email__iexact=email).first()
        if user is None:
            user = User.objects.create_user(
                email=email,
                first_name=profile.get("given_name", ""),
                last_name=profile.get("family_name", ""),
            )
        if user.google_sub != google_sub:
            user.google_sub = google_sub
            user.save(update_fields=["google_sub"])
        refresh = LoginSerializer.get_token(user)
        return Response({"refresh": str(refresh), "access": str(refresh.access_token)})
