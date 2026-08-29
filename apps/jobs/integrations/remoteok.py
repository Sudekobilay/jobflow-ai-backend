import html
import json
import re
from datetime import datetime
from urllib.request import Request, urlopen


REMOTEOK_API_URL = "https://remoteok.com/api"


def _clean_description(value):
    text = html.unescape(value or "")
    return re.sub(r"<[^>]+>", " ", text).strip()


def _parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def fetch_jobs(limit=100, timeout=20):
    request = Request(
        REMOTEOK_API_URL,
        headers={"User-Agent": "JobFlow AI job aggregator/1.0"},
    )
    with urlopen(request, timeout=timeout) as response:
        payload = json.load(response)

    jobs = []
    for item in payload:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        jobs.append(
            {
                "external_id": str(item["id"]),
                "title": item.get("position", "Untitled job")[:200],
                "company": item.get("company", "Unknown company")[:200],
                "location": item.get("location", "Remote")[:200],
                "description": _clean_description(item.get("description")),
                "salary_min": item.get("salary_min") or None,
                "salary_max": item.get("salary_max") or None,
                "is_remote": True,
                "technologies": item.get("tags") or [],
                "source_url": item.get("url") or "",
                "published_at": _parse_datetime(item.get("date")),
            }
        )
        if len(jobs) >= limit:
            break
    return jobs
