from rest_framework import serializers


class AnalyticsOverviewSerializer(serializers.Serializer):
    total_applications = serializers.IntegerField()
    interviews = serializers.IntegerField()
    offers = serializers.IntegerField()
    rejections = serializers.IntegerField()
    success_rate = serializers.FloatField()
    response_rate = serializers.FloatField()