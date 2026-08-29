from rest_framework import serializers

from .models import Job


class JobSerializer(serializers.ModelSerializer):
    match_score = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = Job
        fields = (
            "id",
            "user",
            "title",
            "company",
            "location",
            "description",
            "salary",
            "salary_min",
            "salary_max",
            "is_remote",
            "technologies",
            "experience_level",
            "source",
            "external_id",
            "source_url",
            "published_at",
            "synced_at",
            "created_at",
            "updated_at",
            "match_score",
        )
        read_only_fields = (
            "id",
            "user",
            "source",
            "external_id",
            "source_url",
            "published_at",
            "synced_at",
            "created_at",
            "updated_at",
        )
