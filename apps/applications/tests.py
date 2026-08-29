from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from django.contrib.admin.sites import site
from .cv_parser import extract_cv_data
from .models import CVVersion

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

    def test_cv_parser_extracts_structured_fields(self):
        parsed = extract_cv_data(
            "Ada Lovelace\nada@example.com\n+90 555 123 4567\nhttps://github.com/ada\n"
            "Education\nExperience\nPython Django Docker"
        )

        self.assertEqual(parsed["email"], "ada@example.com")
        self.assertEqual(parsed["github_url"], "https://github.com/ada")
        self.assertIn("python", parsed["skills"])
        self.assertTrue(parsed["education"])

    def test_cv_update_creates_version_snapshot(self):
        cv = self.user.cvs.create(title="Version one", summary="Initial", skills=["Python"])

        response = self.client.patch(reverse("cv-detail", kwargs={"pk": cv.pk}), {"summary": "Updated"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CVVersion.objects.get(cv=cv).summary, "Initial")


class JobApplicationEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="application@example.com", password="StrongPass123")
        self.client.force_authenticate(user=self.user)
        self.cv = self.user.cvs.create(
            title="Backend Developer",
            summary="Python Django backend engineer",
            skills=["Python", "Django"],
        )
        self.job = self.user.jobs_created.create(
            title="Django Engineer",
            company="Test Company",
            location="Istanbul",
            description="Backend dev role.",
            salary="18000",
            is_remote=True,
        )

    def test_create_application_success(self):
        url = reverse("job-application-list-create")
        payload = {
            "job": self.job.pk,
            "cv": self.cv.pk,
            "cover_letter": "I am very interested in this role.",
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["job"], self.job.pk)
        self.assertEqual(response.data["user"], self.user.pk)

    def test_list_applications_is_user_scoped(self):
        application = self.user.job_applications.create(job=self.job, cv=self.cv)

        response = self.client.get(reverse("job-application-list-create"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], application.pk)

    def test_application_status_change_creates_history(self):
        create_response = self.client.post(
            reverse("job-application-list-create"),
            {"job": self.job.pk, "cv": self.cv.pk},
            format="json",
        )
        application_id = create_response.data["id"]

        response = self.client.patch(
            reverse("job-application-detail", kwargs={"pk": application_id}),
            {"status": "interview"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "interview")
        self.assertEqual(len(response.data["status_history"]), 2)
        self.assertEqual(response.data["status_history"][0]["to_status"], "interview")