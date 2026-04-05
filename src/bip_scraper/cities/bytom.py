"""Scraper for Bytom BIP uchwały Rady Miejskiej (kadencja 2024-2029).

Navigation hierarchy:
  KADENCJA_URL (kadencja root)
    └── Year pages (YYYY rok) — filtered to current and previous year
          └── Session pages (uchwaly-rady-miejskiej-z-*)
                └── Paginated act list (ul.aktualnosci-lista)
                      └── Individual acts  (li.aktualnosc__item)

BIP URL: https://www.bytom.pl/bip/
"""

from __future__ import annotations

import html
import re
import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from pydantic import HttpUrl, TypeAdapter

from bip_scraper.models import CitySlug, LegalAct

BASE_URL = "https://www.bytom.pl/bip"
KADENCJA_URL = "https://www.bytom.pl/bip/informacje-rady-miejskiej/kadencja-2024-2029"
YEAR_LINK_RE = re.compile(r"/informacje-rady-miejskiej/(\d{4})-rok$")
SESSION_LINK_RE = re.compile(r"/informacje-rady-miejskiej/uchwaly-rady-miejskiej-z-")
ACT_IDN_RE = re.compile(r"/idn:(\d+)$")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
HTTP_URL_ADAPTER: TypeAdapter[HttpUrl] = TypeAdapter(HttpUrl)


class BytomScraper:
    """Scraper for the Bytom BIP council resolutions portal."""

    def __init__(self, *, timeout_seconds: float = 20.0, max_retries: int = 3) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    @property
    def city(self) -> CitySlug:
        return CitySlug.BYTOM

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        kadencja_html = self._get_text(KADENCJA_URL)
        year_urls = self._parse_year_urls(kadencja_html, now=now)
        if not year_urls:
            raise RuntimeError("Bytom scraper: no year URLs discovered")

        acts: dict[str, LegalAct] = {}
        for year_url in year_urls:
            year_html = self._get_text(year_url)
            session_urls = self._parse_session_urls(year_html)
            for session_url in session_urls:
                for page_html in self._iter_session_pages(session_url):
                    for act in self._parse_session_acts(page_html, now=now):
                        acts[act.stable_id] = act

        if not acts:
            raise RuntimeError("Bytom scraper: no legal acts parsed from session pages")
        return sorted(acts.values(), key=lambda a: a.stable_id)

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
        raise RuntimeError(f"Bytom scraper: request failed for {url}") from last_error

    def _parse_year_urls(self, page_html: str, *, now: datetime) -> list[str]:
        soup = BeautifulSoup(page_html, "html.parser")
        urls: list[str] = []
        for anchor in soup.select("a[href]"):
            href = _normalized_href(anchor.get("href"))
            m = YEAR_LINK_RE.search(href)
            if not m:
                continue
            year = int(m.group(1))
            if year < now.year - 1:
                continue
            absolute_url = urljoin(BASE_URL, href)
            if absolute_url not in urls:
                urls.append(absolute_url)
        return urls

    def _parse_session_urls(self, page_html: str) -> list[str]:
        soup = BeautifulSoup(page_html, "html.parser")
        urls: list[str] = []
        for anchor in soup.select("a[href]"):
            href = _normalized_href(anchor.get("href"))
            if not SESSION_LINK_RE.search(href):
                continue
            # Exclude pagination links (?strona=N) — those belong to the session fetcher
            if "?" in href:
                continue
            absolute_url = href if href.startswith("http") else urljoin(BASE_URL, href)
            if absolute_url not in urls:
                urls.append(absolute_url)
        return urls

    def _iter_session_pages(self, session_url: str):
        """Yield HTML for each pagination page of a session listing."""
        page_html = self._get_text(session_url)
        yield page_html

        soup = BeautifulSoup(page_html, "html.parser")
        next_pages: list[str] = []
        for anchor in soup.select("a[data-ci-pagination-page]"):
            href = _normalized_href(anchor.get("href"))
            absolute = href if href.startswith("http") else urljoin(session_url, href)
            if absolute not in next_pages and absolute != session_url:
                next_pages.append(absolute)

        for page_url in next_pages:
            yield self._get_text(page_url)

    def _parse_session_acts(self, session_html: str, *, now: datetime) -> list[LegalAct]:
        soup = BeautifulSoup(session_html, "html.parser")
        results: list[LegalAct] = []
        for item in soup.select("li.aktualnosc__item"):
            link = item.select_one("a.aktualnosci__link[href]")
            if link is None:
                continue
            href = _normalized_href(link.get("href"))
            m = ACT_IDN_RE.search(href)
            if not m:
                continue
            idn = m.group(1)
            absolute_url = href if href.startswith("http") else urljoin(BASE_URL, href)

            date_span = item.select_one("span.aktualnosci__data")
            date_text = date_span.get_text(strip=True) if date_span else ""
            published_at = _parse_date(date_text, fallback=now)

            title = link.get("title") or link.get_text(" ", strip=True)
            title = title.replace("Przejdź do: ", "").strip()

            results.append(
                LegalAct(
                    stable_id=f"bytom-uchwala-{idn}",
                    title=title,
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


def _parse_date(text: str, *, fallback: datetime) -> datetime:
    m = DATE_RE.search(text)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            pass
    return fallback
