from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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
