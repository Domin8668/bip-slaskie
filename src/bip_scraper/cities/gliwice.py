"""Scraper for Gliwice BIP uchwały Rady Miasta.

BIP URL: https://bip.gliwice.eu/radaMiasta/uchwaly

The ``?rok=YEAR`` parameter does NOT filter by year — it only determines the
starting act (sorted descending by number).  Pagination links never include
the ``rok`` parameter, so all 900+ pages are navigable regardless.

Strategy: paginate from the most-recent page until the page contains only acts
older than ``now.year - 1``, then stop.
"""

from __future__ import annotations

import re
import time
from datetime import UTC, datetime

import httpx
from bs4 import BeautifulSoup
from pydantic import HttpUrl, TypeAdapter

from bip_scraper.models import CitySlug, LegalAct

BASE_URL = "https://bip.gliwice.eu"
ACTS_PATH = "/radaMiasta/uchwaly"
DATE_RE = re.compile(r"Z dnia (\d{2}-\d{2}-\d{4})", re.IGNORECASE)
ACT_ID_RE = re.compile(r"/(\d+)$")

HTTP_URL_ADAPTER: TypeAdapter[HttpUrl] = TypeAdapter(HttpUrl)


class GliwiceScraper:
    """Scraper for the Gliwice BIP council resolutions portal."""

    def __init__(self, *, timeout_seconds: float = 20.0, max_retries: int = 3) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    @property
    def city(self) -> CitySlug:
        return CitySlug.GLIWICE

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        """Fetch and return all uchwały from current and previous year.

        Paginates from page 1 (most recent) and stops as soon as a complete
        page contains no acts from ``now.year`` or ``now.year - 1``.
        """
        min_year = now.year - 1
        acts: dict[str, LegalAct] = {}
        page = 1
        while True:
            url = f"{BASE_URL}{ACTS_PATH}?page={page}"
            html_text = self._get_text(url)
            new_acts = self._parse_acts(html_text)
            # Stop when the page has no acts at all (shouldn't happen) or all
            # acts are older than our cutoff year.
            if not new_acts:
                break
            in_range = [a for a in new_acts if a.published_at.year >= min_year]
            for act in in_range:
                acts[act.stable_id] = act
            # If none of this page's acts are in range, we've gone too far back.
            if not in_range:
                break
            if not self._has_next_page(html_text):
                break
            page += 1

        if not acts:
            raise RuntimeError("Gliwice scraper: no legal acts found")
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
        raise RuntimeError(f"Gliwice scraper: request failed for {url}") from last_error

    def _has_next_page(self, page_html: str) -> bool:
        soup = BeautifulSoup(page_html, "html.parser")
        return soup.find("link", rel="next") is not None or soup.find("a", rel="next") is not None

    def _parse_acts(self, page_html: str) -> list[LegalAct]:
        soup = BeautifulSoup(page_html, "html.parser")
        table = soup.find("table", id="uchwaly")
        if not table:
            return []
        results: list[LegalAct] = []
        for row in table.find_all("tr"):
            opis = row.find("div", class_="uchwaly-opis")
            if not opis:
                continue
            p = opis.find("p")
            if not p:
                continue
            # Extract title from <strong> tag
            strong = p.find("strong")
            if not strong:
                continue
            title = strong.get_text(strip=True)
            if "uchwała" not in title.lower():
                continue
            # Extract date
            p_text = p.get_text(" ", strip=True)
            date_match = DATE_RE.search(p_text)
            if not date_match:
                continue
            published_at = datetime.strptime(date_match.group(1), "%d-%m-%Y").replace(tzinfo=UTC)
            # Extract source URL
            link = p.find("a", href=True)
            if not link:
                continue
            href = link["href"]
            if not href.startswith("http"):
                href = BASE_URL + href
            id_match = ACT_ID_RE.search(href)
            if not id_match:
                continue
            act_id = id_match.group(1)
            source_url = f"{BASE_URL}/rada-miasta/uchwaly/{act_id}"
            results.append(
                LegalAct(
                    stable_id=f"gliwice-uchwala-{act_id}",
                    title=title,
                    published_at=published_at,
                    source_url=HTTP_URL_ADAPTER.validate_python(source_url),
                )
            )
        return results
