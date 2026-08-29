from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class AnalyticsEndpointTests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(email="analytics@example.com", password="StrongPass123")
		other_user = User.objects.create_user(email="other-analytics@example.com", password="StrongPass123")
		self.client.force_authenticate(user=self.user)
		cv = self.user.cvs.create(title="Backend CV", summary="Django", skills=["Django"])
		first_job = self.user.jobs_created.create(
			title="Django Engineer", company="Acme", description="Django", source="manual"
		)
		second_job = self.user.jobs_created.create(
			title="Python Engineer", company="Acme", description="Python", source="manual"
		)
		other_job = other_user.jobs_created.create(
			title="Java Engineer", company="Other", description="Java", source="remoteok"
		)
		self.user.job_applications.create(job=first_job, cv=cv, status="interview")
		self.user.job_applications.create(job=second_job, cv=cv, status="rejected")
		other_cv = other_user.cvs.create(title="Other CV", summary="Java", skills=["Java"])
		other_user.job_applications.create(job=other_job, cv=other_cv, status="offer")

	def test_overview_is_user_scoped_and_calculates_rates(self):
		response = self.client.get(reverse("analytics-overview"))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["total_applications"], 2)
		self.assertEqual(response.data["interviews"], 1)
		self.assertEqual(response.data["offers"], 0)
		self.assertEqual(response.data["rejections"], 1)
		self.assertEqual(response.data["success_rate"], 0.0)
		self.assertEqual(response.data["response_rate"], 100.0)

	def test_status_and_source_aggregations_are_user_scoped(self):
		status_response = self.client.get(reverse("analytics-applications"))
		source_response = self.client.get(reverse("analytics-sources"))

		self.assertEqual(status_response.status_code, status.HTTP_200_OK)
		self.assertEqual(source_response.status_code, status.HTTP_200_OK)
		self.assertEqual(sum(item["count"] for item in status_response.data), 2)
		self.assertEqual(source_response.data, [{"job__source": "manual", "count": 2}])
from django.test import TestCase

# Create your tests here.
