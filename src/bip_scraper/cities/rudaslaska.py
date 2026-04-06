"""Scraper for Ruda Śląska BIP uchwały Rady Miasta.

Navigation: Root → Year pages → Session pages → Individual resolutions.
BIP system: bip.info.pl
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from pydantic import HttpUrl, TypeAdapter

from bip_scraper.cities.base import BaseScraper
from bip_scraper.models import CitySlug, LegalAct

BASE_URL = "https://rudaslaska.bip.info.pl"
ROOT_URL = "https://rudaslaska.bip.info.pl/index.php?idmp=3&r=o"

YEAR_RE = re.compile(r"w (\d{4}) r\.")
SESSION_DATE_RE = re.compile(r"Sesja w dniu (\d{2}\.\d{2}\.\d{4}) r\.", re.IGNORECASE)
IDDOK_RE = re.compile(r"[?&]iddok=(\d+)")
IDMP_RE = re.compile(r"[?&]idmp=(\d+)")

HTTP_URL_ADAPTER: TypeAdapter[HttpUrl] = TypeAdapter(HttpUrl)


class RudaSlaskaScraper(BaseScraper):
    """Scraper for the Ruda Śląska BIP council resolutions portal."""

    _follow_redirects = True

    @property
    def city(self) -> CitySlug:
        return CitySlug.RUDASLASKA

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        """Fetch and return all uchwały from current and previous year."""
        root_html = self._get_text(ROOT_URL)
        year_urls = self._parse_year_urls(root_html, now=now)
        if not year_urls:
            raise RuntimeError("Ruda Slaska scraper: no year URLs found")

        acts: dict[str, LegalAct] = {}
        for year_url in year_urls:
            year_html = self._get_text(year_url)
            session_items = self._parse_session_urls(year_html)
            for session_url, session_date in session_items:
                session_html = self._get_text(session_url)
                for act in self._parse_session_acts(session_html, session_date=session_date):
                    acts[act.stable_id] = act

        if not acts:
            raise RuntimeError("Ruda Slaska scraper: no legal acts found")
        return sorted(acts.values(), key=lambda a: a.stable_id)

    def _parse_year_urls(self, page_html: str, *, now: datetime) -> list[str]:
        soup = BeautifulSoup(page_html, "html.parser")
        urls: list[str] = []
        for anchor in soup.find_all("a", href=True):
            text = anchor.get_text(strip=True)
            m = YEAR_RE.search(text)
            if not m or int(m.group(1)) < now.year - 1:
                continue
            href = anchor["href"]
            absolute_url = urljoin(BASE_URL, href)
            if absolute_url not in urls:
                urls.append(absolute_url)
        return urls

    def _parse_session_urls(self, page_html: str) -> list[tuple[str, datetime]]:
        soup = BeautifulSoup(page_html, "html.parser")
        results: list[tuple[str, datetime]] = []
        for anchor in soup.find_all("a", href=True):
            text = anchor.get_text(strip=True)
            m = SESSION_DATE_RE.search(text)
            if not m:
                continue
            session_date = datetime.strptime(m.group(1), "%d.%m.%Y").replace(tzinfo=UTC)
            href = anchor["href"]
            absolute_url = urljoin(BASE_URL, href)
            if not any(u == absolute_url for u, _ in results):
                results.append((absolute_url, session_date))
        return results

    def _parse_session_acts(self, session_html: str, *, session_date: datetime) -> list[LegalAct]:
        soup = BeautifulSoup(session_html, "html.parser")
        results: list[LegalAct] = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if "dokument.php" not in href:
                continue
            text = anchor.get_text(strip=True)
            if "uchwała" not in text.lower():
                continue
            iddok_m = IDDOK_RE.search(href)
            idmp_m = IDMP_RE.search(href)
            if not iddok_m:
                continue
            iddok = iddok_m.group(1)
            idmp = idmp_m.group(1) if idmp_m else ""
            source_url = f"{BASE_URL}/dokument.php?iddok={iddok}&idmp={idmp}&r=o"
            results.append(
                LegalAct(
                    stable_id=f"rudaslaska-uchwala-{iddok}",
                    title=text,
                    published_at=session_date,
                    source_url=HTTP_URL_ADAPTER.validate_python(source_url),
                )
            )
        return results
