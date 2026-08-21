from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class CVEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="cv@example.com", password="StrongPass123")
        self.client.force_authenticate(user=self.user)

    def test_create_cv_success(self):
        url = reverse("cv-list-create")
        payload = {
            "title": "Senior Backend Developer",
            "summary": "Python/Django backend engineer with 3 years experience.",
            "skills": ["Python", "Django", "REST API"],
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Senior Backend Developer")

    def test_get_cv_detail_success(self):
        cv = self.user.cvs.create(
            title="Fullstack Engineer",
            summary="Experience in Django and React.",
            skills=["Python", "Django", "JavaScript"],
        )

        url = reverse("cv-detail", kwargs={"pk": cv.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Fullstack Engineer")

    def test_update_cv_success(self):
        cv = self.user.cvs.create(
            title="Backend Engineer",
            summary="Initial summary.",
            skills=["Python"],
        )

        url = reverse("cv-detail", kwargs={"pk": cv.pk})
        payload = {
            "title": "Senior Backend Engineer",
            "summary": "Updated summary with Django experience.",
            "skills": ["Python", "Django", "PostgreSQL"],
        }

        response = self.client.put(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Senior Backend Engineer")
        self.assertEqual(response.data["summary"], "Updated summary with Django experience.")

    def test_delete_cv_success(self):
        cv = self.user.cvs.create(
            title="CV to delete",
            summary="This will be deleted.",
            skills=["Python"],
        )

        url = reverse("cv-detail", kwargs={"pk": cv.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(self.user.cvs.filter(pk=cv.pk).exists())

def test_create_application_success(self):
    cv = self.user.cvs.create(
        title="Backend Developer",
        summary="Python Django backend engineer",
        skills=["Python", "Django"]
    )
    job = self.user.jobs_created.create(
        title="Django Engineer",
        company="Test Company",
        location="Istanbul",
        description="Backend dev role.",
        salary="18000",
        is_remote=True,
    )

    url = reverse("job-application-list-create")
    payload = {
        "job": job.pk,
        "cv": cv.pk,
        "cover_letter": "I am very interested in this role."
    }

    response = self.client.post(url, payload, format="json")
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)