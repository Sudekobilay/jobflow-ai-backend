from .models import AIUsage
from decimal import Decimal
from django.conf import settings
import logging


logger = logging.getLogger(__name__)


def _token_count(value):
    return max(0, len(value) // 4)


class AIUsageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated and request.path.startswith("/api/ai/"):
            try:
                request_data = request.data if hasattr(request, "data") else {}
                input_chars = sum(len(str(value)) for value in request_data.values())
                output_text = response.content.decode("utf-8", errors="replace")
                metadata = getattr(request, "ai_usage_metadata", {})
                estimated_input_tokens = _token_count(" ".join(str(value) for value in request_data.values()))
                input_tokens = metadata.get("input_tokens") or estimated_input_tokens
                output_tokens = metadata.get("output_tokens") or _token_count(output_text)
                total_tokens = metadata.get("total_tokens") or input_tokens + output_tokens
                cost = Decimal(str(total_tokens)) * Decimal(str(getattr(settings, "AI_COST_PER_MILLION_TOKENS", "0"))) / Decimal("1000000")
                AIUsage.objects.create(
                    user=request.user,
                    endpoint=request.path,
                    provider=metadata.get("provider", ""),
                    model=metadata.get("model", ""),
                    status_code=response.status_code,
                    input_chars=input_chars,
                    output_chars=len(output_text),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    estimated_cost=cost,
                    outcome=metadata.get("outcome", "success" if response.status_code < 400 else "error"),
                    fallback_reason=metadata.get("fallback_reason", ""),
                    error_type=metadata.get("error_type", ""),
                )
            except Exception:
                logger.exception("AI usage record could not be persisted", extra={"path": request.path})
        return response