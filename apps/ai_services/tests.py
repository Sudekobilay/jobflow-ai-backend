from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import AIUsage
User = get_user_model()


class AIServiceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="ai@example.com", password="StrongPass123")
        self.client.force_authenticate(user=self.user)

    def test_ai_summary_endpoint_success(self):
        url = reverse("ai-summary")
        payload = {"text": "Python, Django, REST API, PostgreSQL geliştiriyorum."}
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("summary", response.data)

    def test_ai_match_endpoint_success(self):
        url = reverse("ai-match")
        payload = {
            "cv_text": "Python, Django, REST API tecrübem var.",
            "job_description": "Python backend geliştirici arıyoruz. Django ve API deneyimi şart."
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("analysis", response.data)

    def test_cv_analysis_is_persisted_for_owned_cv(self):
        cv = self.user.cvs.create(
            title="Backend CV",
            summary="Python Django engineer",
            skills=["Python", "Django"],
        )

        response = self.client.post(reverse("ai-cv-analyze"), {"cv_id": cv.pk}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["cv"], cv.pk)
        self.assertEqual(response.data["status"], "fallback")
        self.assertEqual(self.user.cv_analyses.count(), 1)

    def test_cv_analysis_list_is_user_scoped(self):
        other_user = User.objects.create_user(email="other-ai@example.com", password="StrongPass123")
        self.user.cv_analyses.create(
            ats_score=80,
            strengths=["Django"],
            missing_skills=[],
            recommendations=[],
            status="success",
        )
        other_user.cv_analyses.create(
            ats_score=90,
            strengths=["Java"],
            missing_skills=[],
            recommendations=[],
            status="success",
        )

        response = self.client.get(reverse("ai-cv-analysis-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["ats_score"], 80)

    def test_cover_letter_accepts_cv_and_job_ids(self):
        cv = self.user.cvs.create(
            title="Backend CV",
            summary="Python Django engineer",
            skills=["Python", "Django"],
        )
        job = self.user.jobs_created.create(
            title="Django Engineer",
            company="Example Co",
            description="Build backend APIs with Django.",
        )

        response = self.client.post(
            reverse("ai-cover-letter"),
            {"cv_id": cv.pk, "job_id": job.pk, "language": "en", "tone": "professional"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("cover_letter", response.data)

    def test_assistant_persists_conversation_history(self):
        response = self.client.post(
            reverse("ai-assistant"),
            {"message": "CV'm nasıl?"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        conversation_id = response.data["conversation"]["id"]
        self.assertEqual(len(response.data["conversation"]["messages"]), 2)

        history = self.client.get(reverse("ai-assistant-conversation-detail", kwargs={"pk": conversation_id}))
        self.assertEqual(history.status_code, status.HTTP_200_OK)
        self.assertEqual(len(history.data["messages"]), 2)

    def test_match_by_ids_is_persisted_and_listed(self):
        cv = self.user.cvs.create(title="Python CV", summary="Python Django", skills=["Python", "Django"])
        job = self.user.jobs_created.create(
            title="Django Engineer", company="Acme", description="Python Django Docker", technologies=["Python", "Django", "Docker"]
        )

        response = self.client.post(reverse("ai-match"), {"cv_id": cv.pk, "job_id": job.pk}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["match_score"], 0)
        self.assertLessEqual(response.data["match_score"], 100)
        self.assertEqual(response.data["matching_skills"], ["python", "django"])
        history = self.client.get(reverse("ai-match-list"))
        self.assertEqual(history.status_code, status.HTTP_200_OK)
        self.assertEqual(len(history.data), 1)

    def test_usage_report_returns_token_cost_and_outcome_totals(self):
        AIUsage.objects.create(
            user=self.user,
            endpoint="/api/ai/summary/",
            provider="groq.com",
            model="test-model",
            status_code=200,
            input_chars=40,
            output_chars=80,
            input_tokens=10,
            output_tokens=20,
            total_tokens=30,
            estimated_cost="0.00030000",
            outcome="fallback",
            fallback_reason="provider_not_configured",
        )

        response = self.client.get(reverse("ai-usage-report"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"]["total_tokens"], 30)
        self.assertEqual(response.data["total"]["output_tokens"], 20)
        self.assertEqual(response.data["total"]["estimated_cost"], "0.00030000")
        self.assertEqual(response.data["outcomes"], [{"outcome": "fallback", "count": 1}])
