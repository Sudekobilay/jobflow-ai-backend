from rest_framework import serializers

from apps.applications.models import CV, JobApplication

from .models import EmailDelivery, EmailDraft


class EmailDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailDraft
        fields = (
            "id", "recipient_email", "subject", "body", "cv", "application",
            "status", "approved_at", "sent_at", "last_error", "created_at", "updated_at",
        )
        read_only_fields = ("id", "status", "approved_at", "sent_at", "last_error", "created_at", "updated_at")

    def validate(self, attrs):
        user = self.context["request"].user
        cv = attrs.get("cv")
        application = attrs.get("application")
        if cv and cv.user_id != user.id:
            raise serializers.ValidationError({"cv": "Bu CV size ait değil."})
        if application and application.user_id != user.id:
            raise serializers.ValidationError({"application": "Bu başvuru size ait değil."})
        if application and cv and application.cv_id != cv.id:
            raise serializers.ValidationError("CV başvuru ile eşleşmiyor.")
        return attrs


class EmailDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailDelivery
        fields = "__all__"
        read_only_fields = ("id", "draft", "status", "error_message", "attempt_count", "next_retry_at", "delivered_at")