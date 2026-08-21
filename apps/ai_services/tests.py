from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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
