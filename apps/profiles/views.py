from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import Certificate, Language, Skill, UserProfile
from .serializers import (
    CertificateRelationSerializer,
    ProfileRelationSerializer,
    UserProfileSerializer,
)


class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class ProfileRelationView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    relation_name = ""
    model = None
    serializer_class = ProfileRelationSerializer

    def get(self, request, *args, **kwargs):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return Response(getattr(profile, self.relation_name).values("id", "name"))

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        relation, _ = self.model.objects.get_or_create(name=serializer.validated_data["name"])
        getattr(profile, self.relation_name).add(relation)
        return Response({"id": relation.id, "name": relation.name}, status=201)


class SkillProfileView(ProfileRelationView):
    relation_name = "skills"
    model = Skill


class LanguageProfileView(ProfileRelationView):
    relation_name = "languages"
    model = Language


class CertificateProfileView(ProfileRelationView):
    relation_name = "certificates"
    model = Certificate
    serializer_class = CertificateRelationSerializer

    def get(self, request, *args, **kwargs):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return Response(profile.certificates.values("id", "name", "issuer"))

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        relation, _ = Certificate.objects.get_or_create(
            name=serializer.validated_data["name"],
            defaults={"issuer": serializer.validated_data.get("issuer", "")},
        )
        getattr(profile, self.relation_name).add(relation)
        return Response(
            {"id": relation.id, "name": relation.name, "issuer": relation.issuer},
            status=201,
        )


class ProfileCompletionView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        checks = {
            "first_name": bool(profile.first_name), "last_name": bool(profile.last_name),
            "phone": bool(profile.phone), "university": bool(profile.university),
            "department": bool(profile.department), "gpa": profile.gpa is not None,
            "bio": bool(profile.bio), "github_url": bool(profile.github_url),
            "linkedin_url": bool(profile.linkedin_url), "skills": profile.skills.exists(),
            "certificates": profile.certificates.exists(), "languages": profile.languages.exists(),
        }
        completed = sum(checks.values())
        return Response({
            "percentage": round(completed * 100 / len(checks)),
            "completed_fields": [field for field, present in checks.items() if present],
            "missing_fields": [field for field, present in checks.items() if not present],
        })