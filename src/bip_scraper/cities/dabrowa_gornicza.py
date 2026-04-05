"""Scraper for Dąbrowa Górnicza BIP uchwały Rady Miejskiej (IX kadencja, 2024-2029).

BIP URL: https://www.bip.dabrowa-gornicza.pl/181640
Paginated at: /181640/strona/N
"""

from __future__ import annotations

import re
import time
from datetime import UTC, datetime

import httpx
from bs4 import BeautifulSoup
from pydantic import HttpUrl, TypeAdapter

from bip_scraper.models import CitySlug, LegalAct

BASE_URL = "https://www.bip.dabrowa-gornicza.pl"
ACTS_ROOT = f"{BASE_URL}/181640"
DOC_ID_RE = re.compile(r"181640/dokument/(\d+)")

HTTP_URL_ADAPTER: TypeAdapter[HttpUrl] = TypeAdapter(HttpUrl)


class DabrowaGorniczaScraper:
    """Scraper for the Dąbrowa Górnicza BIP council resolutions portal."""

    def __init__(self, *, timeout_seconds: float = 20.0, max_retries: int = 3) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

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

    def _get_text(self, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                # verify=False needed: server sends incomplete certificate chain
                response = httpx.get(url, timeout=self.timeout_seconds, follow_redirects=True, verify=False)
                response.raise_for_status()
                return response.text
            except (httpx.TimeoutException, httpx.HTTPError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(2)
        raise RuntimeError(f"Dabrowa Gornicza scraper: request failed for {url}") from last_error

    def _parse_acts(self, page_html: str) -> list[LegalAct]:
        soup = BeautifulSoup(page_html, "html.parser")
        results: list[LegalAct] = []
        for div in soup.find_all("div", class_=lambda c: c and "list_date-sym" in c):
            # Extract symbol
            symbol_span = div.find("span", class_="text-uppercase")
            if not symbol_span:
                continue
            symbol = symbol_span.get_text(strip=True)

            # Extract date
            date_div = div.find("div", class_=lambda c: c and "text-right" in c)
            if not date_div:
                continue
            date_text = date_div.get_text(strip=True)
            try:
                published_at = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=UTC)
            except ValueError:
                continue

            # Extract subject and document link
            link = div.find("a", class_="router_link")
            if not link:
                continue
            subject = link.get_text(strip=True)
            href = link.get("href", "")
            doc_id_match = DOC_ID_RE.search(href)
            if not doc_id_match:
                continue
            doc_id = doc_id_match.group(1)

            title = f"Uchwała {symbol} {subject}"
            source_url = f"{BASE_URL}/181640/dokument/{doc_id}"

            results.append(
                LegalAct(
                    stable_id=f"dabrowa-gornicza-uchwala-{doc_id}",
                    title=title,
                    published_at=published_at,
                    source_url=HTTP_URL_ADAPTER.validate_python(source_url),
                )
            )
        return results
