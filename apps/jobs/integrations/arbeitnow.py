import html
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ARBEITNOW_API_URL = "https://www.arbeitnow.com/api/job-board-api"


def _clean_description(value):
    text = html.unescape(value or "")
    return re.sub(r"<[^>]+>", " ", text).strip()


def _parse_datetime(value):
    if not value:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def fetch_jobs(limit=100, timeout=20):
    query = urlencode({"page": 1})
    request = Request(
        f"{ARBEITNOW_API_URL}?{query}",
        headers={"User-Agent": "JobFlow AI job aggregator/1.0"},
    )
    with urlopen(request, timeout=timeout) as response:
        payload = json.load(response)

    jobs = []
    for item in payload.get("data", []):
        if not item.get("slug") and not item.get("url"):
            continue
        external_id = item.get("slug") or item["url"]
        jobs.append(
            {
                "external_id": str(external_id),
                "title": item.get("title", "Untitled job")[:200],
                "company": item.get("company_name", "Unknown company")[:200],
                "location": item.get("location", "")[:200],
                "description": _clean_description(item.get("description")),
                "is_remote": bool(item.get("remote")) or "remote" in item.get("location", "").lower(),
                "technologies": item.get("tags") or [],
                "source_url": item.get("url", ""),
                "published_at": _parse_datetime(item.get("created_at")),
            }
        )
        if len(jobs) >= limit:
            break
    return jobs
