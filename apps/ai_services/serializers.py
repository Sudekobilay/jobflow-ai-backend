from rest_framework import serializers


class AISummarySerializer(serializers.Serializer):
    text = serializers.CharField(help_text="Özetlenecek metin", allow_blank=False)


class AISummaryResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    summary = serializers.CharField()
    status = serializers.CharField()
    error = serializers.CharField(required=False, allow_blank=True)


class AIMatchSerializer(serializers.Serializer):
    cv_text = serializers.CharField(help_text="Adayın CV metni", allow_blank=False)
    job_description = serializers.CharField(help_text="İş ilanı metni", allow_blank=False)


class AIMatchResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    analysis = serializers.CharField()
    match_score = serializers.IntegerField(required=False)
    status = serializers.CharField()
    error = serializers.CharField(required=False, allow_blank=True)
