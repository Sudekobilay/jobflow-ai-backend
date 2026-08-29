from rest_framework import serializers
from .models import UserProfile, Skill, Certificate, Language


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = "__all__"


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = "__all__"


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = "__all__"


class UserProfileSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)
    certificates = CertificateSerializer(many=True, read_only=True)
    languages = LanguageSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "user",
            "first_name",
            "last_name",
            "phone",
            "university",
            "department",
            "gpa",
            "bio",
            "github_url",
            "linkedin_url",
            "experience_years",
            "skills",
            "certificates",
            "languages",
        )
        read_only_fields = ("id", "user", "skills", "certificates", "languages")


class ProfileRelationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)


class CertificateRelationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    issuer = serializers.CharField(max_length=200, required=False, allow_blank=True)