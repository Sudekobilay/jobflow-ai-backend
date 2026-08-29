from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class JobEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="job@example.com", password="StrongPass123")
        self.client.force_authenticate(user=self.user)

    def test_create_job_success(self):
        url = reverse("job-list-create")
        payload = {
            "title": "Django Backend Developer",
            "company": "JobFlow AI",
            "location": "Istanbul",
            "description": "Build Python backend APIs and integrate AI workflows.",
            "salary": "15000",
            "is_remote": True,
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Django Backend Developer")

    def test_get_job_detail_success(self):
        job = self.user.jobs_created.create(
            title="Python Developer",
            company="OpenAI Partner",
            location="Remote",
            description="Build backend services with Python.",
            salary="18000",
            is_remote=True,
        )

        url = reverse("job-detail", kwargs={"pk": job.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["company"], "OpenAI Partner")

    def test_update_job_success(self):
        job = self.user.jobs_created.create(
            title="Backend Engineer",
            company="Old Company",
            location="Istanbul",
            description="Old description.",
            salary="12000",
            is_remote=False,
        )

        url = reverse("job-detail", kwargs={"pk": job.pk})
        payload = {
            "title": "Senior Backend Engineer",
            "company": "New Company",
            "location": "Remote",
            "description": "Updated description for remote backend work.",
            "salary": "22000",
            "is_remote": True,
        }

        response = self.client.put(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Senior Backend Engineer")
        self.assertEqual(response.data["company"], "New Company")

    def test_delete_job_success(self):
        job = self.user.jobs_created.create(
            title="Job to delete",
            company="Delete Me Ltd.",
            location="Ankara",
            description="This should be removed.",
            salary="10000",
            is_remote=False,
        )

        url = reverse("job-detail", kwargs={"pk": job.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(self.user.jobs_created.filter(pk=job.pk).exists())

    def test_other_user_cannot_update_job(self):
        other_user = User.objects.create_user(email="other@example.com", password="StrongPass123")
        job = self.user.jobs_created.create(
            title="Owned Job",
            company="Original Company",
            location="Istanbul",
            description="Original description.",
            salary="15000",
            is_remote=False,
        )

        self.client.force_authenticate(user=other_user)
        url = reverse("job-detail", kwargs={"pk": job.pk})
        response = self.client.patch(url, {"title": "Hacked Title"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        job.refresh_from_db()
        self.assertEqual(job.title, "Owned Job")

    def test_list_jobs_filter_success(self):
        self.user.jobs_created.create(
            title="Python Backend Developer",
            company="Alpha Labs",
            location="Istanbul",
            description="Python API work with Django.",
            salary="18000",
            is_remote=True,
        )
        self.user.jobs_created.create(
            title="Frontend Engineer",
            company="Beta Studio",
            location="Ankara",
            description="React and UI design.",
            salary="20000",
            is_remote=False,
        )
        self.user.jobs_created.create(
            title="Data Engineer",
            company="Gamma AI",
            location="Istanbul",
            description="Build data pipelines and backend services.",
            salary="25000",
            is_remote=True,
        )

        url = reverse("job-list-create")
        response = self.client.get(
            url,
            {
                "search": "python",
                "location": "istanbul",
                "is_remote": "true",
                "min_salary": "15000",
                "max_salary": "22000",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Python Backend Developer")

    def test_list_jobs_can_be_ranked_by_match_score(self):
        cv = self.user.cvs.create(title="Python CV", summary="Python", skills=["Python"])
        lower = self.user.jobs_created.create(
            title="Python Job", company="Alpha", description="Python Django", is_active=True
        )
        higher = self.user.jobs_created.create(
            title="Python Docker Job", company="Beta", description="Python Django Docker", is_active=True
        )
        from apps.ai_services.models import JobMatch

        JobMatch.objects.create(user=self.user, cv=cv, job=lower, match_score=50)
        JobMatch.objects.create(user=self.user, cv=cv, job=higher, match_score=90)

        response = self.client.get(reverse("job-list-create"), {"match_cv_id": cv.pk})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], higher.pk)
        self.assertEqual(response.data[0]["match_score"], 90)

    def test_expired_jobs_are_hidden(self):
        expired = self.user.jobs_created.create(
            title="Expired", company="Old", description="No longer available",
            expires_at=timezone.now() - timedelta(days=1), is_active=False,
        )

        response = self.client.get(reverse("job-list-create"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(expired.pk, [item["id"] for item in response.data])
