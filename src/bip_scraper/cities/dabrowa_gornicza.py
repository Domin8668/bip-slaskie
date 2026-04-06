"""Scraper for Dąbrowa Górnicza BIP uchwały Rady Miejskiej (IX kadencja, 2024-2029).

BIP URL: https://www.bip.dabrowa-gornicza.pl/181640
Paginated at: /181640/strona/N
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

import httpx
from bs4 import BeautifulSoup
from pydantic import HttpUrl, TypeAdapter

from bip_scraper.cities.base import BaseScraper
from bip_scraper.models import CitySlug, LegalAct

BASE_URL = "https://www.bip.dabrowa-gornicza.pl"
ACTS_ROOT = f"{BASE_URL}/181640"
DOC_ID_RE = re.compile(r"181640/dokument/(\d+)")

HTTP_URL_ADAPTER: TypeAdapter[HttpUrl] = TypeAdapter(HttpUrl)


class DabrowaGorniczaScraper(BaseScraper):
    """Scraper for the Dąbrowa Górnicza BIP council resolutions portal."""

    @property
    def city(self) -> CitySlug:
        return CitySlug.DABROWAG

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        """Fetch and return all uchwały."""
        _ = now
        acts: dict[str, LegalAct] = {}
        page = 1
        while True:
            if page == 1:
                url = ACTS_ROOT
            else:
                url = f"{ACTS_ROOT}/strona/{page}"
            html_text = self._get_text(url)
            new_acts = self._parse_acts(html_text)
            if not new_acts:
                break
            for act in new_acts:
                acts[act.stable_id] = act
            page += 1

        if not acts:
            raise RuntimeError("Dabrowa Gornicza scraper: no legal acts found")
        return sorted(acts.values(), key=lambda a: a.stable_id)

    def _make_request(self, url: str) -> httpx.Response:
        # verify=False needed: server sends incomplete certificate chain
        return httpx.get(url, timeout=self.timeout_seconds, follow_redirects=True, verify=False)

    def _parse_acts(self, page_html: str) -> list[LegalAct]:
        soup = BeautifulSoup(page_html, "html.parser")
        results: list[LegalAct] = []
        for div in soup.find_all("div", class_=lambda c: c and "list_date-sym" in c):
            act = _parse_div(div)
            if act:
                results.append(act)
        return results


def _parse_div(div) -> LegalAct | None:
    # Extract symbol
    symbol_span = div.find("span", class_="text-uppercase")
    if not symbol_span:
        return None
    symbol = symbol_span.get_text(strip=True)

    # Extract date
    date_div = div.find("div", class_=lambda c: c and "text-right" in c)
    if not date_div:
        return None
    date_text = date_div.get_text(strip=True)
    try:
        published_at = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        return None

    # Extract subject and document link
    link = div.find("a", class_="router_link")
    if not link:
        return None
    subject = link.get_text(strip=True)
    href = link.get("href", "")
    doc_id_match = DOC_ID_RE.search(href)
    if not doc_id_match:
        return None
    doc_id = doc_id_match.group(1)

    title = f"Uchwała {symbol} {subject}"
    source_url = f"{BASE_URL}/181640/dokument/{doc_id}"

    return LegalAct(
        stable_id=f"dabrowa-gornicza-uchwala-{doc_id}",
        title=title,
        published_at=published_at,
        source_url=HTTP_URL_ADAPTER.validate_python(source_url),
    )
