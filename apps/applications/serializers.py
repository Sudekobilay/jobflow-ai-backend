from pathlib import Path

from rest_framework import serializers

from apps.jobs.models import Job

from .models import ApplicationNote, ApplicationReminder, ApplicationStatusHistory, CV, CVAnalysis, CVVersion, Interview, JobApplication, Offer
from .cv_parser import parse_cv_file, validate_cv_content


class CVSerializer(serializers.ModelSerializer):
    class Meta:
        model = CV
        fields = (
            "id",
            "user",
            "title",
            "summary",
            "skills",
            "file",
            "file_type",
            "parsed_text",
            "parsed_data",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "file_type", "parsed_text", "parsed_data", "created_at", "updated_at")

    def validate_file(self, uploaded_file):
        allowed_types = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
        allowed_extensions = {".pdf", ".docx"}
        extension = Path(uploaded_file.name).suffix.lower()
        if extension not in allowed_extensions or uploaded_file.content_type not in allowed_types:
            raise serializers.ValidationError("Yalnızca geçerli PDF veya DOCX dosyaları desteklenir.")
        if uploaded_file.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("CV dosyası 5 MB'dan büyük olamaz.")
        try:
            validate_cv_content(uploaded_file)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))
        return uploaded_file

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        uploaded_file = validated_data.get("file")
        if uploaded_file:
            try:
                parsed_text, file_type, parsed_data = parse_cv_file(uploaded_file)
            except ValueError as exc:
                raise serializers.ValidationError({"file": str(exc)})
            validated_data["parsed_text"] = parsed_text
            validated_data["file_type"] = file_type
            validated_data["parsed_data"] = parsed_data
        return super().create(validated_data)

    def update(self, instance, validated_data):
        uploaded_file = validated_data.get("file")
        if uploaded_file:
            try:
                parsed_text, file_type, parsed_data = parse_cv_file(uploaded_file)
            except ValueError as exc:
                raise serializers.ValidationError({"file": str(exc)})
            validated_data["parsed_text"] = parsed_text
            validated_data["file_type"] = file_type
            validated_data["parsed_data"] = parsed_data
        CVVersion.objects.create(
            cv=instance, title=instance.title, summary=instance.summary, skills=instance.skills,
            parsed_text=instance.parsed_text, parsed_data=instance.parsed_data,
            version_number=instance.versions.count() + 1,
        )
        return super().update(instance, validated_data)


class CVVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVVersion
        fields = ("id", "cv", "version_number", "title", "summary", "skills", "parsed_text", "parsed_data", "created_at")
        read_only_fields = fields


class JobApplicationSerializer(serializers.ModelSerializer):
    status_history = serializers.SerializerMethodField()

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
            "status_history",
        )
        read_only_fields = ("id", "user", "created_at", "updated_at")

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        application = super().create(validated_data)
        ApplicationStatusHistory.objects.create(to_status=application.status, application=application)
        return application

    def update(self, instance, validated_data):
        previous_status = instance.status
        application = super().update(instance, validated_data)
        if application.status != previous_status:
            ApplicationStatusHistory.objects.create(
                application=application,
                from_status=previous_status,
                to_status=application.status,
            )
        return application

    def get_status_history(self, obj):
        return [
            {
                "from_status": entry.from_status,
                "to_status": entry.to_status,
                "changed_at": entry.changed_at,
            }
            for entry in obj.status_history.all()
        ]


class CVAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVAnalysis
        fields = (
            "id",
            "user",
            "cv",
            "ats_score",
            "strengths",
            "missing_skills",
            "recommendations",
            "status",
            "error",
            "created_at",
        )
        read_only_fields = fields


class ApplicationNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationNote
        fields = "__all__"
        read_only_fields = ("id", "created_at")


class ApplicationReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationReminder
        fields = "__all__"


class InterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = "__all__"


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = "__all__"