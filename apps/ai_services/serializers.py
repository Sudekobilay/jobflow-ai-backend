from rest_framework import serializers
from .models import AssistantConversation, AssistantMessage, JobMatch


class AISummarySerializer(serializers.Serializer):
    text = serializers.CharField(help_text="Özetlenecek metin", allow_blank=False)


class AISummaryResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    summary = serializers.CharField()
    status = serializers.CharField()
    error = serializers.CharField(required=False, allow_blank=True)


class AIMatchSerializer(serializers.Serializer):
    cv_id = serializers.IntegerField(required=False)
    job_id = serializers.IntegerField(required=False)
    cv_text = serializers.CharField(required=False, allow_blank=False, help_text="Adayın CV metni")
    job_description = serializers.CharField(required=False, allow_blank=False, help_text="İş ilanı metni")

    def validate(self, attrs):
        if not attrs.get("cv_id") and not attrs.get("cv_text"):
            raise serializers.ValidationError("cv_id veya cv_text alanlarından biri zorunludur.")
        if not attrs.get("job_id") and not attrs.get("job_description"):
            raise serializers.ValidationError("job_id veya job_description alanlarından biri zorunludur.")
        return attrs


class AIMatchResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    analysis = serializers.CharField()
    match_score = serializers.IntegerField(required=False)
    status = serializers.CharField()
    error = serializers.CharField(required=False, allow_blank=True)


class JobMatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobMatch
        fields = ("id", "cv", "job", "match_score", "matching_skills", "missing_skills", "explanation", "status", "created_at")
        read_only_fields = fields


class AICVAnalyzeSerializer(serializers.Serializer):
    cv_id = serializers.IntegerField(required=False)
    cv_text = serializers.CharField(required=False, allow_blank=False)

    def validate(self, attrs):
        if not attrs.get("cv_id") and not attrs.get("cv_text"):
            raise serializers.ValidationError("cv_id veya cv_text alanlarından biri zorunludur.")
        return attrs


class AICVAnalyzeResponseSerializer(serializers.Serializer):
    ats_score = serializers.IntegerField()
    strengths = serializers.ListField(child=serializers.CharField())
    missing_skills = serializers.ListField(child=serializers.CharField())
    recommendations = serializers.ListField(child=serializers.CharField())
    status = serializers.CharField()
    error = serializers.CharField(required=False, allow_blank=True)


class AICoverLetterSerializer(serializers.Serializer):
    cv_id = serializers.IntegerField(required=False)
    job_id = serializers.IntegerField(required=False)
    cv_text = serializers.CharField(required=False, allow_blank=False)
    job_description = serializers.CharField(required=False, allow_blank=False)
    language = serializers.CharField(required=False, default="en")
    tone = serializers.CharField(required=False, default="professional")

    def validate(self, attrs):
        if not attrs.get("cv_id") and not attrs.get("cv_text"):
            raise serializers.ValidationError("cv_id veya cv_text alanlarından biri zorunludur.")
        if not attrs.get("job_id") and not attrs.get("job_description"):
            raise serializers.ValidationError("job_id veya job_description alanlarından biri zorunludur.")
        return attrs


class AICoverLetterResponseSerializer(serializers.Serializer):
    cover_letter = serializers.CharField()
    status = serializers.CharField()
    error = serializers.CharField(required=False, allow_blank=True)


class AssistantMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantMessage
        fields = ("id", "role", "content", "created_at")
        read_only_fields = fields


class AssistantConversationSerializer(serializers.ModelSerializer):
    messages = AssistantMessageSerializer(many=True, read_only=True)

    class Meta:
        model = AssistantConversation
        fields = ("id", "title", "messages", "created_at", "updated_at")
        read_only_fields = fields


class AssistantRequestSerializer(serializers.Serializer):
    message = serializers.CharField(allow_blank=False)
    conversation_id = serializers.IntegerField(required=False)
    cv_id = serializers.IntegerField(required=False)
    job_id = serializers.IntegerField(required=False)
