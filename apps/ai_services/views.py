import json
import os

from django.db.models import Count, Sum
from django.utils import timezone
from openai import OpenAI
from rest_framework import generics, permissions, status, throttling
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .serializers import (
    AISummarySerializer,
    AISummaryResponseSerializer,
    AIMatchSerializer,
    AIMatchResponseSerializer,
    AICVAnalyzeSerializer,
    AICVAnalyzeResponseSerializer,
    AICoverLetterSerializer,
    AICoverLetterResponseSerializer,
    JobMatchSerializer,
)
from apps.applications.models import CV, CVAnalysis
from apps.jobs.models import Job
from apps.applications.serializers import CVAnalysisSerializer
from .models import AIUsage, AssistantConversation, AssistantMessage, JobMatch
from .serializers import AssistantConversationSerializer, AssistantRequestSerializer


class AIUserRateThrottle(throttling.UserRateThrottle):
    scope = "ai"


def _get_ai_client():
    api_key = os.getenv("GROQ_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    if not api_key:
        return None
    return OpenAI(
        api_key=api_key,
        base_url=os.getenv("AI_BASE_URL", "https://api.groq.com/openai/v1"),
    )


def _get_ai_model():
    return os.getenv("AI_MODEL", "openai/gpt-oss-20b")


def _set_ai_usage_metadata(request, provider_response=None, outcome="success", fallback_reason="", error_type=""):
    usage = getattr(provider_response, "usage", None) if provider_response is not None else None
    get_value = lambda name: getattr(usage, name, 0) if usage is not None else 0
    request.ai_usage_metadata = {
        "provider": os.getenv("AI_BASE_URL", "").split("//")[-1].split("/")[0],
        "model": _get_ai_model(),
        "input_tokens": get_value("prompt_tokens"),
        "output_tokens": get_value("completion_tokens"),
        "total_tokens": get_value("total_tokens"),
        "outcome": outcome,
        "fallback_reason": fallback_reason,
        "error_type": error_type,
    }


def _fallback_analysis(cv_text):
    lowered = cv_text.lower()
    known_skills = [skill for skill in ("python", "django", "java", "spring", "docker", "sql", "aws") if skill in lowered]
    missing_skills = [skill for skill in ("docker", "unit testing", "ci/cd") if skill not in lowered]
    return {
        "ats_score": min(95, 55 + len(known_skills) * 5),
        "strengths": known_skills,
        "missing_skills": missing_skills,
        "recommendations": [f"Consider adding {skill} experience." for skill in missing_skills],
        "status": "fallback",
    }


def _match_skills(cv_text, job_description):
    skill_names = ("python", "django", "java", "spring", "docker", "sql", "aws", "react", "flutter", "kubernetes", "unit testing", "ci/cd")
    cv_lower = cv_text.lower()
    job_lower = job_description.lower()
    required = [skill for skill in skill_names if skill in job_lower]
    matching = [skill for skill in required if skill in cv_lower]
    missing = [skill for skill in required if skill not in cv_lower]
    score = round(len(matching) * 100 / len(required)) if required else 50
    return score, matching, missing


def _normalize_match_result(result, fallback_score, fallback_matching, fallback_missing):
    result["match_score"] = max(0, min(100, int(result.get("match_score", fallback_score))))
    result["matching_skills"] = [str(skill).strip().lower() for skill in result.get("matching_skills", fallback_matching)]
    result["missing_skills"] = [str(skill).strip().lower() for skill in result.get("missing_skills", fallback_missing)]
    result.setdefault("explanation", "AI tarafından oluşturulan eşleşme analizi.")
    return result


@extend_schema(
    summary="AI özeti",
    description="Verilen metni özetleyen AI endpoint'i.",
    tags=["AI"],
    request=AISummarySerializer,
    responses=AISummaryResponseSerializer,
)
class AISummaryView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIUserRateThrottle]
    serializer_class = AISummarySerializer

    def post(self, request, *args, **kwargs):
        text = request.data.get("text", "").strip()
        if not text:
            return Response({"detail": "text alanı zorunludur."}, status=status.HTTP_400_BAD_REQUEST)

        client = _get_ai_client()
        if client is None:
            _set_ai_usage_metadata(request, outcome="fallback", fallback_reason="provider_not_configured")
            return Response({
                "message": "AI summary generated successfully (fallback mode)",
                "summary": f"Bu adayın özeti: {text[:200]}...",
                "status": "fallback",
            }, status=status.HTTP_200_OK)

        try:
            response = client.chat.completions.create(
                model=_get_ai_model(),
                messages=[
                    {"role": "system", "content": "Kısa, net ve profesyonel bir CV özeti üret."},
                    {"role": "user", "content": text},
                ],
                temperature=0.3,
            )
            _set_ai_usage_metadata(request, response)
            summary = response.choices[0].message.content.strip()
            return Response({
                "message": "AI summary generated successfully",
                "summary": summary,
                "status": "success",
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            _set_ai_usage_metadata(request, outcome="fallback", fallback_reason="provider_error", error_type=type(exc).__name__)
            return Response({
                "message": "AI summary generated successfully (fallback mode)",
                "summary": f"Bu adayın özeti: {text[:200]}...",
                "status": "fallback",
                "error": str(exc),
            }, status=status.HTTP_200_OK)

@extend_schema(
    summary="AI eşleşme analizi",
    description="CV metni ile iş ilanı metnini karşılaştırır ve uyum oranını çıkarır.",
    tags=["AI"],
    request=AIMatchSerializer,
    responses=AIMatchResponseSerializer,
)
class AIMatchView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIUserRateThrottle]
    serializer_class = AIMatchSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        cv = CV.objects.filter(pk=data.get("cv_id"), user=request.user).first() if data.get("cv_id") else None
        if data.get("cv_id") and cv is None:
            return Response({"detail": "CV bulunamadı."}, status=status.HTTP_404_NOT_FOUND)
        job = Job.objects.filter(pk=data.get("job_id"), is_active=True).first() if data.get("job_id") else None
        if data.get("job_id") and job is None:
            return Response({"detail": "İlan bulunamadı."}, status=status.HTTP_404_NOT_FOUND)
        cv_text = data.get("cv_text") or "\n".join((cv.title, cv.summary, "Skills: " + ", ".join(cv.skills), cv.parsed_text))
        job_description = data.get("job_description") or f"{job.title} at {job.company}\n{job.description}\nTechnologies: {', '.join(job.technologies)}"
        score, matching, missing = _match_skills(cv_text, job_description)

        client = _get_ai_client()
        if client is None:
            _set_ai_usage_metadata(request, outcome="fallback", fallback_reason="provider_not_configured")
            result = {"match_score": score, "matching_skills": matching, "missing_skills": missing,
                      "explanation": "Beceri kesişimine göre hesaplanan eşleşme.", "status": "fallback"}
            match = JobMatch.objects.create(user=request.user, cv=cv, job=job, **result) if job else None
            return Response({"message": "Job match analysis generated successfully (fallback mode)", "analysis": result["explanation"], **(JobMatchSerializer(match).data if match else result)}, status=status.HTTP_200_OK)

        try:
            prompt = (
                "Return only valid JSON with match_score (integer 0-100), matching_skills (array), missing_skills (array), explanation (string). "
                f"CV:\n{cv_text}\n\nİş İlanı:\n{job_description}"
            )
            response = client.chat.completions.create(
                model=_get_ai_model(),
                messages=[
                    {"role": "system", "content": "Analyze job fit and return the requested JSON schema."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            _set_ai_usage_metadata(request, response)
            content = response.choices[0].message.content.strip().strip("`")
            result = json.loads(content)
            result = _normalize_match_result(result, score, matching, missing)
            result["status"] = "success"
            match = JobMatch.objects.create(user=request.user, cv=cv, job=job, **result) if job else None
            return Response({"message": "Job match analysis generated successfully", "analysis": result["explanation"], **(JobMatchSerializer(match).data if match else result)}, status=status.HTTP_200_OK)
        except Exception as exc:
            _set_ai_usage_metadata(request, outcome="fallback", fallback_reason="provider_error", error_type=type(exc).__name__)
            result = {"match_score": score, "matching_skills": matching, "missing_skills": missing,
                      "explanation": "AI yanıtı işlenemedi; beceri kesişimine göre hesaplandı.", "status": "fallback", "error": str(exc)}
            match = JobMatch.objects.create(user=request.user, cv=cv, job=job, **{key: value for key, value in result.items() if key != "error"}) if job else None
            return Response({"message": "Job match analysis generated successfully (fallback mode)", "analysis": result["explanation"], **(JobMatchSerializer(match).data if match else result)}, status=status.HTTP_200_OK)


class JobMatchListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = JobMatchSerializer

    def get_queryset(self):
        return JobMatch.objects.filter(user=self.request.user).select_related("job", "cv")


class JobMatchDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = JobMatchSerializer

    def get_queryset(self):
        return JobMatch.objects.filter(user=self.request.user)


@extend_schema(
    summary="CV analizi",
    description="CV metnini ATS ve yetenekler açısından analiz eder.",
    tags=["AI"],
    request=AICVAnalyzeSerializer,
    responses=AICVAnalyzeResponseSerializer,
)
class AICVAnalyzeView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIUserRateThrottle]
    serializer_class = AICVAnalyzeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cv = None
        if serializer.validated_data.get("cv_id"):
            cv = CV.objects.filter(pk=serializer.validated_data["cv_id"], user=request.user).first()
            if cv is None:
                return Response({"detail": "CV bulunamadı."}, status=status.HTTP_404_NOT_FOUND)
            cv_text = "\n".join((cv.title, cv.summary, "Skills: " + ", ".join(cv.skills)))
        else:
            cv_text = serializer.validated_data["cv_text"].strip()
        if not cv_text:
            return Response({"detail": "cv_text alanı zorunludur."}, status=status.HTTP_400_BAD_REQUEST)
        client = _get_ai_client()
        fallback = _fallback_analysis(cv_text)
        if client is None:
            _set_ai_usage_metadata(request, outcome="fallback", fallback_reason="provider_not_configured")
            analysis = CVAnalysis.objects.create(user=request.user, cv=cv, **fallback)
            return Response(CVAnalysisSerializer(analysis).data, status=status.HTTP_201_CREATED)
        try:
            response = client.chat.completions.create(
                model=_get_ai_model(),
                messages=[
                    {"role": "system", "content": "Analyze the CV and return JSON with ats_score, strengths, missing_skills, recommendations."},
                    {"role": "user", "content": cv_text},
                ],
                temperature=0.2,
                max_tokens=500,
            )
            _set_ai_usage_metadata(request, response)
            result = json.loads(response.choices[0].message.content)
            result["status"] = "success"
            analysis = CVAnalysis.objects.create(user=request.user, cv=cv, **result)
            return Response(CVAnalysisSerializer(analysis).data, status=status.HTTP_201_CREATED)
        except Exception as exc:
            _set_ai_usage_metadata(request, outcome="fallback", fallback_reason="provider_response_invalid", error_type=type(exc).__name__)
            fallback["error"] = str(exc)
            analysis = CVAnalysis.objects.create(user=request.user, cv=cv, **fallback)
            return Response(CVAnalysisSerializer(analysis).data, status=status.HTTP_201_CREATED)


class CVAnalysisListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CVAnalysisSerializer

    def get_queryset(self):
        return CVAnalysis.objects.filter(user=self.request.user)


class CVAnalysisDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CVAnalysisSerializer

    def get_queryset(self):
        return CVAnalysis.objects.filter(user=self.request.user)


class AssistantConversationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssistantConversationSerializer

    def get_queryset(self):
        return AssistantConversation.objects.filter(user=self.request.user)


class AssistantConversationDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssistantConversationSerializer

    def get_queryset(self):
        return AssistantConversation.objects.filter(user=self.request.user)


class AssistantChatView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIUserRateThrottle]
    serializer_class = AssistantRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        conversation = AssistantConversation.objects.filter(
            pk=data.get("conversation_id"), user=request.user
        ).first() if data.get("conversation_id") else None
        if conversation is None:
            conversation = AssistantConversation.objects.create(user=request.user)
        user_message = AssistantMessage.objects.create(conversation=conversation, role="user", content=data["message"])
        context = ""
        if data.get("cv_id"):
            cv = CV.objects.filter(pk=data["cv_id"], user=request.user).first()
            if cv:
                context += f"\nCV: {cv.summary}; skills: {', '.join(cv.skills)}"
        if data.get("job_id"):
            job = Job.objects.filter(pk=data["job_id"]).first()
            if job:
                context += f"\nJob: {job.title} at {job.company}: {job.description}"
        client = _get_ai_client()
        if client:
            try:
                response = client.chat.completions.create(
                    model=_get_ai_model(),
                    messages=[
                        {"role": "system", "content": "You are a concise, practical career assistant."},
                        {"role": "user", "content": data["message"] + context},
                    ],
                    temperature=0.3,
                )
                _set_ai_usage_metadata(request, response)
                answer = response.choices[0].message.content.strip()
            except Exception as exc:
                _set_ai_usage_metadata(request, outcome="fallback", fallback_reason="provider_error", error_type=type(exc).__name__)
                answer = "AI servisine şu anda ulaşılamıyor. Lütfen daha sonra tekrar deneyin."
        else:
            _set_ai_usage_metadata(request, outcome="fallback", fallback_reason="provider_not_configured")
            answer = "Profilinizi, CV'nizi ve hedef ilanı birlikte inceleyerek kariyer önerileri sunabilirim."
        AssistantMessage.objects.create(conversation=conversation, role="assistant", content=answer)
        conversation.save(update_fields=["updated_at"])
        return Response({"conversation": AssistantConversationSerializer(conversation).data, "message": answer})


@extend_schema(
    summary="Cover letter üretimi",
    description="CV ve iş ilanına göre ilana özel ön yazı üretir.",
    tags=["AI"],
    request=AICoverLetterSerializer,
    responses=AICoverLetterResponseSerializer,
)
class AICoverLetterView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIUserRateThrottle]
    serializer_class = AICoverLetterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        cv = None
        job = None
        if data.get("cv_id"):
            cv = CV.objects.filter(pk=data["cv_id"], user=request.user).first()
            if cv is None:
                return Response({"detail": "CV bulunamadı."}, status=status.HTTP_404_NOT_FOUND)
            cv_text = "\n".join((cv.title, cv.summary, "Skills: " + ", ".join(cv.skills)))
        else:
            cv_text = data["cv_text"].strip()
        if data.get("job_id"):
            job = Job.objects.filter(pk=data["job_id"]).first()
            if job is None:
                return Response({"detail": "İlan bulunamadı."}, status=status.HTTP_404_NOT_FOUND)
            job_description = f"{job.title} at {job.company}\n{job.description}"
        else:
            job_description = data["job_description"].strip()
        if not cv_text or not job_description:
            return Response({"detail": "cv_text ve job_description alanları zorunludur."}, status=400)
        client = _get_ai_client()
        if client is None:
            _set_ai_usage_metadata(request, outcome="fallback", fallback_reason="provider_not_configured")
            return Response({"cover_letter": f"Dear Hiring Manager,\n\nI am excited to apply based on my experience: {cv_text[:300]}", "status": "fallback"})
        try:
            response = client.chat.completions.create(
                model=_get_ai_model(),
                messages=[
                    {"role": "system", "content": f"Write a concise {data['tone']} cover letter in {data['language']}."},
                    {"role": "user", "content": f"CV:\n{cv_text}\n\nJob:\n{job_description}"},
                ],
                temperature=0.3,
                max_tokens=600,
            )
            _set_ai_usage_metadata(request, response)
            return Response({"cover_letter": response.choices[0].message.content.strip(), "status": "success"})
        except Exception as exc:
            _set_ai_usage_metadata(request, outcome="fallback", fallback_reason="provider_error", error_type=type(exc).__name__)
            return Response({"cover_letter": "Unable to generate cover letter right now.", "status": "fallback", "error": str(exc)})


class AIUsageReportView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        usage = AIUsage.objects.filter(user=request.user)
        today = timezone.localdate()
        month_start = today.replace(day=1)

        def totals(queryset):
            values = queryset.aggregate(
                requests=Count("id"),
                input_tokens=Sum("input_tokens"),
                output_tokens=Sum("output_tokens"),
                total_tokens=Sum("total_tokens"),
                estimated_cost=Sum("estimated_cost"),
            )
            values["estimated_cost"] = f"{values['estimated_cost'] or 0:.8f}"
            return {key: (value or 0) for key, value in values.items()}

        return Response({
            "total": totals(usage),
            "today": totals(usage.filter(created_at__date=today)),
            "this_month": totals(usage.filter(created_at__date__gte=month_start)),
            "outcomes": list(usage.values("outcome").annotate(count=Count("id")).order_by("outcome")),
        })
