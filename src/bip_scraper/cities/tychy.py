"""Scraper for Tychy BIP uchwały Rady Miasta (kadencja 2024-2029).

Navigation hierarchy:
  ACTS_INDEX_URL (kadencja root listing)
    └── Month pages (uchwaly-rady-miasta/32/YEAR/MONTH) — current and previous year
          └── Individual act links (uchwaly-rady-miasta/ID)

Note: bip.umtychy.pl uses a certificate from home.pl DV TLS CA which is not
in all default trust stores; verify=False is used to bypass TLS verification
on this known official government domain.

BIP URL: https://bip.umtychy.pl/
"""

from __future__ import annotations

import re
import warnings
from datetime import UTC, datetime
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from pydantic import HttpUrl, TypeAdapter

from bip_scraper.cities.base import BaseScraper
from bip_scraper.cities.base import normalized_href as _normalized_href
from bip_scraper.models import CitySlug, LegalAct

BASE_URL = "https://bip.umtychy.pl"
ACTS_INDEX_URL = "https://bip.umtychy.pl/uchwaly-rady-miasta"
# Current kadencja (IX, 2024-2029) uses numeric ID 32 in the URL path
CURRENT_KADENCJA_MONTH_RE = re.compile(r"uchwaly-rady-miasta/32/(\d{4})/(\d{1,2})$")
ACT_ID_RE = re.compile(r"uchwaly-rady-miasta/(\d+)$")
POLISH_MONTHS = {
    "stycznia": 1,
    "lutego": 2,
    "marca": 3,
    "kwietnia": 4,
    "maja": 5,
    "czerwca": 6,
    "lipca": 7,
    "sierpnia": 8,
    "września": 9,
    "października": 10,
    "listopada": 11,
    "grudnia": 12,
}
DATE_RE = re.compile(
    r"z\s+dnia\s+(\d{1,2})\s+(" + "|".join(POLISH_MONTHS) + r")\s+(\d{4})\s+r\.",
    re.IGNORECASE,
)
HTTP_URL_ADAPTER: TypeAdapter[HttpUrl] = TypeAdapter(HttpUrl)


class TychyScraper(BaseScraper):
    """Scraper for the Tychy BIP council resolutions portal."""

    @property
    def city(self) -> CitySlug:
        return CitySlug.TYCHY

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        index_html = self._get_text(ACTS_INDEX_URL)
        month_urls = self._parse_month_urls(index_html, now=now)
        if not month_urls:
            raise RuntimeError("Tychy scraper: no month URLs discovered")

        acts: dict[str, LegalAct] = {}
        for month_url in month_urls:
            month_html = self._get_text(month_url)
            for act in self._parse_month_acts(month_html, now=now):
                acts[act.stable_id] = act

        if not acts:
            raise RuntimeError("Tychy scraper: no legal acts parsed from month pages")
        return sorted(acts.values(), key=lambda a: a.stable_id)

    def _make_request(self, url: str) -> httpx.Response:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return httpx.get(
                url,
                timeout=self.timeout_seconds,
                follow_redirects=True,
                verify=False,
            )

    def _parse_month_urls(self, page_html: str, *, now: datetime) -> list[str]:
        soup = BeautifulSoup(page_html, "html.parser")
        urls: list[str] = []
        for anchor in soup.select("a[href]"):
            href = _normalized_href(anchor.get("href"))
            m = CURRENT_KADENCJA_MONTH_RE.search(href)
            if not m or int(m.group(1)) < now.year - 1:
                continue
            absolute_url = urljoin(BASE_URL, href)
            if absolute_url not in urls:
                urls.append(absolute_url)
        return urls

    def _parse_month_acts(self, month_html: str, *, now: datetime) -> list[LegalAct]:
        soup = BeautifulSoup(month_html, "html.parser")
        results: list[LegalAct] = []
        for row in soup.select("tr"):
            link = row.select_one("td a[href]")
            if link is None:
                continue
            href = _normalized_href(link.get("href"))
            m = ACT_ID_RE.search(href)
            if not m:
                continue
            act_id = m.group(1)
            absolute_url = urljoin(BASE_URL, href)

            title = link.get_text(" ", strip=True)
            published_at = _parse_polish_date(title, fallback=now)

            results.append(
                LegalAct(
                    stable_id=f"tychy-uchwala-{act_id}",
                    title=title,
                    published_at=published_at,
                    source_url=HTTP_URL_ADAPTER.validate_python(absolute_url),
                )
            )
        return results


def _parse_polish_date(text: str, *, fallback: datetime) -> datetime:
    m = DATE_RE.search(text)
    if m:
        day = int(m.group(1))
        month = POLISH_MONTHS.get(m.group(2).lower(), 0)
        year = int(m.group(3))
        if month:
            try:
                return datetime(year, month, day, tzinfo=UTC)
            except ValueError:
                pass
    return fallback
