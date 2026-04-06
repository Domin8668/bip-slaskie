from __future__ import annotations

import html
import re
import time
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.parse import parse_qs, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from pydantic import HttpUrl, TypeAdapter

from bip_scraper.models import CitySlug, LegalAct

_DATE_RE = re.compile(r"(\d{2}\.\d{2}\.\d{4})")
_HTTP_URL_ADAPTER: TypeAdapter[HttpUrl] = TypeAdapter(HttpUrl)


class CityScraper(Protocol):
    @property
    def city(self) -> CitySlug: ...

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]: ...


class BaseScraper:  # pylint: disable=too-few-public-methods
    """Shared HTTP helper for all city scrapers."""

    _follow_redirects: bool = False
    _verify_ssl: bool = True

    def __init__(self, *, timeout_seconds: float = 20.0, max_retries: int = 3) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def _make_request(self, url: str) -> httpx.Response:
        return httpx.get(
            url,
            timeout=self.timeout_seconds,
            follow_redirects=self._follow_redirects,
            verify=self._verify_ssl,
        )

    def _get_text(self, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._make_request(url)
                response.raise_for_status()
                return response.text
            except (httpx.TimeoutException, httpx.HTTPError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(2)
        raise RuntimeError(f"{type(self).__name__}: request failed for {url}") from last_error


def normalized_href(value: Any) -> str:
    if isinstance(value, str):
        return html.unescape(value).strip()
    if isinstance(value, list):
        return html.unescape(" ".join(str(v) for v in value)).strip()
    return ""


def is_act_text(text: str) -> bool:
    upper_text = text.upper()
    return "UCHWAŁA" in upper_text or "RESOLUTION" in upper_text


def extract_stable_id(url: str) -> str | None:
    parsed = urlparse(url)
    for param in ["id", "idr", "uchwala", "document", "kat"]:
        values = parse_qs(parsed.query).get(param, [])
        if values:
            return values[0]
    path_parts = parsed.path.rstrip("/").split("/")
    for part in reversed(path_parts):
        if part and (part.isdigit() or "-" in part):
            return part
    return None


def extract_date_from_text(text: str, *, fallback: datetime) -> datetime:
    match = _DATE_RE.search(text)
    if match:
        try:
            return datetime.strptime(match.group(1), "%d.%m.%Y").replace(tzinfo=UTC)
        except ValueError:
            pass
    return fallback


def parse_acts_from_links(
    page_html: str,
    *,
    base_url: str,
    stable_id_prefix: str,
    now: datetime,
) -> list[LegalAct]:
    """Parse LegalAct instances from qualifying anchor links in page_html."""
    soup = BeautifulSoup(page_html, "html.parser")
    results: list[LegalAct] = []
    for link in soup.select("a[href]"):
        text = link.get_text(strip=True)
        if not is_act_text(text):
            continue
        href = normalized_href(link.get("href"))
        if not href:
            continue
        source_url = urljoin(base_url, href)
        stable_id = extract_stable_id(source_url)
        if not stable_id:
            continue
        published_at = extract_date_from_text(text, fallback=now)
        results.append(
            LegalAct(
                stable_id=f"{stable_id_prefix}-{stable_id}",
                title=text,
                published_at=published_at,
                source_url=_HTTP_URL_ADAPTER.validate_python(source_url),
            )
        )
    return results
