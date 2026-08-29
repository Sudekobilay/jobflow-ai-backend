from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.models import JobApplication
from apps.ai_services.models import AIUsage, JobMatch


class UserApplicationsMixin:
	def get_queryset(self):
		return JobApplication.objects.filter(user=self.request.user)


class AnalyticsOverviewView(UserApplicationsMixin, APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		applications = self.get_queryset()
		total = applications.count()
		interviews = applications.filter(status="interview").count()
		offers = applications.filter(status__in=("offer", "accepted")).count()
		rejections = applications.filter(status="rejected").count()
		responded = applications.exclude(status__in=("saved", "to_apply", "applied")).count()
		response_hours = [
			(entry.changed_at - application.created_at).total_seconds() / 3600
			for application in applications
			for entry in application.status_history.all()
			if entry.from_status
		]
		ai_usage = AIUsage.objects.filter(user=request.user)
		matches = JobMatch.objects.filter(user=request.user)
		return Response({
			"total_applications": total,
			"interviews": interviews,
			"offers": offers,
			"rejections": rejections,
			"success_rate": round(offers * 100 / total, 2) if total else 0.0,
			"response_rate": round(responded * 100 / total, 2) if total else 0.0,
			"average_response_hours": round(sum(response_hours) / len(response_hours), 2) if response_hours else 0.0,
			"ai_requests": ai_usage.count(),
			"ai_estimated_cost": f"{ai_usage.aggregate(total=Sum('estimated_cost'))['total'] or 0:.8f}",
			"average_match_score": round(matches.aggregate(total=Sum('match_score'))['total'] / matches.count(), 2) if matches.exists() else 0.0,
		})


class ApplicationAnalyticsView(UserApplicationsMixin, APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		return Response(list(self.get_queryset().values("status").annotate(count=Count("id")).order_by("status")))


class SourceAnalyticsView(UserApplicationsMixin, APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		queryset = self.get_queryset()
		if request.query_params.get("detailed") != "true":
			return Response(list(queryset.values("job__source").annotate(count=Count("id")).order_by("job__source")))
		rows = []
		for source in queryset.values_list("job__source", flat=True).distinct():
			items = queryset.filter(job__source=source)
			offers = items.filter(status__in=("offer", "accepted")).count()
			rows.append({"source": source, "total": items.count(), "offers": offers, "success_rate": round(offers * 100 / items.count(), 2) if items.count() else 0.0})
		return Response(rows)


class TimelineAnalyticsView(UserApplicationsMixin, APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		timeline = self.get_queryset().annotate(month=TruncMonth("created_at")).values("month").annotate(count=Count("id")).order_by("month")
		return Response([
			{"month": item["month"].date().isoformat(), "count": item["count"]}
			for item in timeline
		])
