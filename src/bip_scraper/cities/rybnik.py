"""Scraper for Rybnik BIP uchwały Rady Miasta.

Navigation: single-page registry table at Default.aspx?Page=247 with all
historical resolutions. Acts are filtered to the current and previous year.

BIP URL: https://bip.um.rybnik.eu/
"""

from __future__ import annotations

import html
import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from pydantic import HttpUrl, TypeAdapter

from bip_scraper.models import CitySlug, LegalAct

BASE_URL = "https://bip.um.rybnik.eu"
ACTS_URL = "https://bip.um.rybnik.eu/Default.aspx?Page=247"
HTTP_URL_ADAPTER: TypeAdapter[HttpUrl] = TypeAdapter(HttpUrl)


class RybnikScraper:
    """Scraper for the Rybnik BIP council resolutions portal."""

    def __init__(self, *, timeout_seconds: float = 30.0, max_retries: int = 3) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    @property
    def city(self) -> CitySlug:
        return CitySlug.RYBNIK

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        page_html = self._get_text(ACTS_URL)
        acts = self._parse_acts(page_html, now=now)
        if not acts:
            raise RuntimeError("Rybnik scraper: no legal acts parsed from the registry page")
        return sorted(acts, key=lambda a: a.stable_id)

    def _get_text(self, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = httpx.get(url, timeout=self.timeout_seconds, follow_redirects=True)
                response.raise_for_status()
                return response.text
            except (httpx.TimeoutException, httpx.HTTPError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(2)
        raise RuntimeError(f"Rybnik scraper: request failed for {url}") from last_error

    def _parse_acts(self, page_html: str, *, now: datetime) -> list[LegalAct]:
        soup = BeautifulSoup(page_html, "html.parser")
        min_year = now.year - 1
        results: list[LegalAct] = []

        # The first registry table contains the resolutions
        table = soup.select_one("table.registry")
        if table is None:
            return results

        for row in table.select("tbody tr"):
            cells = row.select("td")
            if len(cells) < 4:
                continue

            number_text = cells[0].get_text(strip=True)
            date_text = cells[1].get_text(strip=True)
            title_text = cells[2].get_text(" ", strip=True)
            detail_link = cells[3].select_one("a[href]")

            if not date_text or not detail_link:
                continue

            published_at = _parse_date(date_text)
            if published_at is None or published_at.year < min_year:
                continue

            href = _normalized_href(detail_link.get("href"))
            absolute_url = urljoin(BASE_URL, href)
            act_id = _extract_id_param(href)
            if act_id is None:
                continue

            full_title = f"{number_text} — {title_text}" if number_text else title_text

            results.append(
                LegalAct(
                    stable_id=f"rybnik-uchwala-{act_id}",
                    title=full_title,
                    published_at=published_at,
                    source_url=HTTP_URL_ADAPTER.validate_python(absolute_url),
                )
            )
        return results


def _normalized_href(value: Any) -> str:
    if isinstance(value, str):
        return html.unescape(value).strip()
    if isinstance(value, list):
        return html.unescape(" ".join(str(v) for v in value)).strip()
    return ""


def _parse_date(text: str) -> datetime | None:
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        return None


def _extract_id_param(href: str) -> str | None:
    parsed = urlparse(href)
    values = parse_qs(parsed.query).get("Id", [])
    return values[0] if values else None
