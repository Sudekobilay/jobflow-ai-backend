import html
import json
import os
import re
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ADZUNA_API_TEMPLATE = "https://api.adzuna.com/v1/api/jobs/{country}/search/1"


def _clean_description(value):
    text = html.unescape(value or "")
    return re.sub(r"<[^>]+>", " ", text).strip()


def _parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def fetch_jobs(limit=100, timeout=20):
    app_id = os.getenv("ADZUNA_APP_ID", "")
    app_key = os.getenv("ADZUNA_APP_KEY", "")
    if not app_id or not app_key:
        raise RuntimeError("ADZUNA_APP_ID and ADZUNA_APP_KEY must be set")

    country = os.getenv("ADZUNA_COUNTRY", "gb")
    query = urlencode(
        {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": min(limit, 50),
            "what": os.getenv("ADZUNA_QUERY", ""),
            "content-type": "application/json",
        }
    )
    request = Request(
        f"{ADZUNA_API_TEMPLATE.format(country=country)}?{query}",
        headers={"User-Agent": "JobFlow AI job aggregator/1.0"},
    )
    with urlopen(request, timeout=timeout) as response:
        payload = json.load(response)

    jobs = []
    for item in payload.get("results", []):
        if not item.get("id"):
            continue
        location = item.get("location", {}).get("display_name", "")
        category = item.get("category", {}).get("label", "")
        jobs.append(
            {
                "external_id": str(item["id"]),
                "title": item.get("title", "Untitled job")[:200],
                "company": item.get("company", {}).get("display_name", "Unknown company")[:200],
                "location": location[:200],
                "description": _clean_description(item.get("description")),
                "salary_min": item.get("salary_min"),
                "salary_max": item.get("salary_max"),
                "is_remote": "remote" in f"{location} {item.get('title', '')}".lower(),
                "technologies": [category] if category else [],
                "source_url": item.get("redirect_url", ""),
                "published_at": _parse_datetime(item.get("created")),
            }
        )
        if len(jobs) >= limit:
            break
    return jobs
