from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.utils import extend_schema
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer

User = get_user_model()

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
