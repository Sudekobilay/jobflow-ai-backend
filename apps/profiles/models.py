from django.conf import settings
from django.db import models


class Skill(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Certificate(models.Model):
    name = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name


class Language(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    university = models.CharField(max_length=200, blank=True, null=True)
    department = models.CharField(max_length=200, blank=True, null=True)
    gpa = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    experience_years = models.IntegerField(default=0)
    skills = models.ManyToManyField(Skill, blank=True)
    certificates = models.ManyToManyField(Certificate, blank=True)
    languages = models.ManyToManyField(Language, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} profile"