from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import UserProfile
from .serializers import UserProfileSerializer


class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile