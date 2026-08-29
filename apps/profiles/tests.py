from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class ProfileUpdateTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="profile@example.com",
            password="StrongPass123",
            first_name="Ali",
            last_name="Yilmaz",
        )
        self.client.force_authenticate(user=self.user)

    def test_update_profile_success(self):
        url = reverse("profile-me")
        payload = {
            "first_name": "Ahmet",
            "last_name": "Demir",
            "phone": "+905551234567",
            "university": "Istanbul Technical University",
            "department": "Computer Engineering",
            "gpa": "3.80",
            "bio": "Backend engineer",
            "github_url": "https://github.com/ahmet",
            "linkedin_url": "https://linkedin.com/in/ahmet",
            "experience_years": 2,
        }

        response = self.client.put(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.first_name, "Ahmet")
        self.assertEqual(self.user.profile.university, "Istanbul Technical University")
        self.assertEqual(self.user.profile.experience_years, 2)

    def test_manage_profile_relations(self):
        skill_response = self.client.post(reverse("profile-skills"), {"name": "Django"}, format="json")
        language_response = self.client.post(reverse("profile-languages"), {"name": "English"}, format="json")
        certificate_response = self.client.post(
            reverse("profile-certificates"),
            {"name": "AWS Cloud Practitioner", "issuer": "AWS"},
            format="json",
        )

        self.assertEqual(skill_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(language_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(certificate_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self.client.get(reverse("profile-skills")).data), 1)
        self.assertEqual(len(self.client.get(reverse("profile-languages")).data), 1)
        self.assertEqual(len(self.client.get(reverse("profile-certificates")).data), 1)
