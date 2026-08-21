from rest_framework import serializers

from apps.jobs.models import Job

from .models import CV, JobApplication


class CVSerializer(serializers.ModelSerializer):
    class Meta:
        model = CV
        fields = (
            "id",
            "user",
            "title",
            "summary",
            "skills",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "created_at", "updated_at")

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class JobApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = (
            "id",
            "user",
            "job",
            "cv",
            "status",
            "cover_letter",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "created_at", "updated_at")

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)