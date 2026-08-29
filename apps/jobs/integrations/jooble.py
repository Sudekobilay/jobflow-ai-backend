import html
import json
import os
import re
from datetime import datetime
from urllib.request import Request, urlopen


JOOBLE_API_URL = "https://jooble.org/api/{key}"


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
    api_key = os.getenv("JOOBLE_APP_KEY", "")
    if not api_key:
        raise RuntimeError("JOOBLE_APP_KEY must be set")

    payload = json.dumps(
        {
            "keywords": os.getenv("JOOBLE_KEYWORDS", "python django"),
            "location": os.getenv("JOOBLE_LOCATION", ""),
            "page": 1,
        }
    ).encode("utf-8")
    request = Request(
        JOOBLE_API_URL.format(key=api_key),
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "JobFlow AI job aggregator/1.0",
        },
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        data = json.load(response)

    jobs = []
    for index, item in enumerate(data.get("jobs", [])):
        title = item.get("title", "Untitled job")
        company = item.get("company", "Unknown company")
        location = item.get("location", "")
        source_url = item.get("link", "")
        external_id = item.get("id") or source_url or f"{title}:{company}:{index}"
        jobs.append(
            {
                "external_id": str(external_id),
                "title": title[:200],
                "company": company[:200],
                "location": location[:200],
                "description": _clean_description(item.get("snippet")),
                "salary": item.get("salary", "")[:100],
                "is_remote": "remote" in f"{title} {location}".lower(),
                "technologies": [],
                "source_url": source_url,
                "published_at": _parse_datetime(item.get("updated")),
            }
        )
        if len(jobs) >= limit:
            break
    return jobs
