from __future__ import annotations

import html
import re
import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from pydantic import HttpUrl, TypeAdapter

from bip_scraper.models import CitySlug, LegalAct

BASE_URL = "https://www.siemianowice.pl"
UCHWALY_LIST_URL = f"{BASE_URL}/bip/rada-miasta/uchwaly/"

# Matches Uchwała title - captures number and potential date info
ACT_TITLE_RE = re.compile(
    r"UCHWAŁA\s+(?:Nr|NR|nr|z\s+dnia)\s+([\w/\s\.,-]+?)(?:\s+z\s+dnia\s+(\d{2}\.\d{2}\.\d{4}))?",
    re.IGNORECASE,
)

# Matches date in Polish format
DATE_RE = re.compile(r"(\d{2}\.\d{2}\.\d{4})")

HTTP_URL_ADAPTER: TypeAdapter[HttpUrl] = TypeAdapter(HttpUrl)


class SiemianowiceScraper:
    """Scraper for Siemianowice Śląskie BIP council resolutions portal."""

    def __init__(self, *, timeout_seconds: float = 20.0, max_retries: int = 3) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    @property
    def city(self) -> CitySlug:
        return CitySlug.SIEMIANOWICE

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        """Fetch and return all uchwały from the city council."""
        try:
            list_html = self._get_text(UCHWALY_LIST_URL)
            acts = self._parse_acts_from_html(list_html, now=now)
            if not acts:
                raise RuntimeError("Siemianowice scraper: no legal acts parsed")
            return sorted(acts, key=lambda a: a.stable_id)
        except Exception as exc:
            raise RuntimeError(f"Siemianowice scraper: failed to scrape acts") from exc

    def _get_text(self, url: str) -> str:
        """Fetch *url* and return its text body, retrying on transient errors."""
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = httpx.get(url, timeout=self.timeout_seconds)
                response.raise_for_status()
                return response.text
            except (httpx.TimeoutException, httpx.HTTPError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(2)
        raise RuntimeError(f"Siemianowice scraper: request failed for {url}") from last_error

    def _parse_acts_from_html(self, page_html: str, *, now: datetime) -> list[LegalAct]:
        """Parse uchwały from the main listing page."""
        soup = BeautifulSoup(page_html, "html.parser")
        results: list[LegalAct] = []

        # Look for common patterns: links containing "uchwała" or documents section
        for link in soup.select("a[href]"):
            text = link.get_text(strip=True)
            if not _is_act_text(text):
                continue

            href = _normalized_href(link.get("href"))
            if not href:
                continue

            # Convert to absolute URL
            source_url = urljoin(BASE_URL, href)

            # Extract a stable ID from the URL
            stable_id = _extract_stable_id(source_url)
            if not stable_id:
                continue

            # Extract publish date from text if available
            published_at = _extract_date_from_text(text, fallback=now)

            results.append(
                LegalAct(
                    stable_id=f"siemianowice-uchwala-{stable_id}",
                    title=text,
                    published_at=published_at,
                    source_url=HTTP_URL_ADAPTER.validate_python(source_url),
                )
            )

        return results


def _is_act_text(text: str) -> bool:
    """Check if text appears to be a council resolution."""
    upper_text = text.upper()
    return "UCHWAŁA" in upper_text or "RESOLUTION" in upper_text


def _normalized_href(value: Any) -> str:
    """Safely extract and unescape an href attribute value."""
    if isinstance(value, str):
        return html.unescape(value).strip()
    if isinstance(value, list):
        return html.unescape(" ".join(str(item) for item in value)).strip()
    return ""


def _extract_stable_id(url: str) -> str | None:
    """Extract a stable ID from the URL (document ID, slug, etc.)."""
    parsed = urlparse(url)

    # Try common query parameters first
    for param in ["id", "idr", "uchwala", "document", "kat"]:
        values = parse_qs(parsed.query).get(param, [])
        if values:
            return values[0]

    # Try to extract from path if it contains numeric or slug-like components
    path_parts = parsed.path.rstrip("/").split("/")
    for part in reversed(path_parts):
        if part and (part.isdigit() or "-" in part):
            return part

    return None


def _extract_date_from_text(text: str, *, fallback: datetime) -> datetime:
    """Extract date from text in Polish format (DD.MM.YYYY)."""
    match = DATE_RE.search(text)
    if match:
        try:
            return datetime.strptime(match.group(1), "%d.%m.%Y").replace(tzinfo=UTC)
        except ValueError:
            pass
    return fallback
