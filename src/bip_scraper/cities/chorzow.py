"""Scraper for Chorzów BIP uchwały Rady Miasta (IX kadencja, 2024-2029).

Navigation hierarchy:
  YEARS_URL (IX kadencja root)
    └── Year pages (ROK 20XX) — filtered to current and previous year
          └── Session pages (SESJA I, SESJA II, …)
                └── Individual act links (UCHWAŁA …)
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup
from pydantic import HttpUrl, TypeAdapter

from bip_scraper.cities.base import BaseScraper
from bip_scraper.cities.base import normalized_href as _normalized_href
from bip_scraper.models import CitySlug, LegalAct

BASE_URL = "https://bip.chorzow.eu"

# IX kadencja (2024-2029) acts root page — lists year sub-pages
YEARS_URL = "https://bip.chorzow.eu/index.php?kat=171559651914468222"

# Matches "ROK 2025", "ROK 2026", etc. in menu anchor text
YEAR_LABEL_RE = re.compile(r"\bROK\s+(20\d{2})\b", re.IGNORECASE)

# Matches UCHWAŁA title text, capturing resolution number and date
ACT_TITLE_RE = re.compile(
    r"UCHWAŁA\s+(?:Nr|NR|nr)\s+([\w/]+)\s+z\s+dnia\s+(\d{2}\.\d{2}\.\d{4})",
    re.IGNORECASE,
)

HTTP_URL_ADAPTER: TypeAdapter[HttpUrl] = TypeAdapter(HttpUrl)


class ChorzowScraper(BaseScraper):
    """Scraper for the Chorzów BIP council resolutions portal."""

    @property
    def city(self) -> CitySlug:
        return CitySlug.CHORZOW

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        """Fetch and return all uchwały from current and previous year."""
        years_html = self._get_text(YEARS_URL)
        year_urls = self._parse_year_urls_from_html(years_html, now=now)
        if not year_urls:
            raise RuntimeError("Chorzow scraper: no year URLs discovered")

        acts: dict[str, LegalAct] = {}
        for year_url in year_urls:
            year_html = self._get_text(year_url)
            session_urls = self._parse_session_urls_from_html(year_html)
            for session_url in session_urls:
                session_html = self._get_text(session_url)
                for act in self._parse_session_acts(session_html, now=now):
                    acts[act.stable_id] = act

        if not acts:
            raise RuntimeError("Chorzow scraper: no legal acts parsed from session pages")
        return sorted(acts.values(), key=lambda a: a.stable_id)

    # ------------------------------------------------------------------
    # Parsing helpers (also used directly in tests)
    # ------------------------------------------------------------------

    def _parse_year_urls_from_html(self, page_html: str, *, now: datetime) -> list[str]:
        """Return absolute URLs for year sub-pages >= *now*.year - 1."""
        soup = BeautifulSoup(page_html, "html.parser")
        maincontent = soup.find(id="maincontent") or soup
        urls: list[str] = []
        for anchor in maincontent.select("li.W2K a[id]"):
            text = anchor.get_text(strip=True)
            m = YEAR_LABEL_RE.search(text)
            if not m or int(m.group(1)) < now.year - 1:
                continue
            anchor_id = _normalized_href(anchor.get("id"))
            id_match = re.match(r"^ka(\d+)\.\d+$", anchor_id)
            if not id_match:
                continue
            kat_id = id_match.group(1)
            absolute_url = f"{BASE_URL}/index.php?kat={kat_id}"
            if absolute_url not in urls:
                urls.append(absolute_url)
        return urls

    def _parse_session_urls_from_html(self, page_html: str) -> list[str]:
        """Return absolute session-page URLs from a year listing page."""
        soup = BeautifulSoup(page_html, "html.parser")
        maincontent = soup.find(id="maincontent") or soup
        urls: list[str] = []
        for anchor in maincontent.select("li.W2K a[id]"):
            text = anchor.get_text(strip=True)
            if not text.upper().startswith("SESJA"):
                continue
            anchor_id = _normalized_href(anchor.get("id"))
            id_match = re.match(r"^ka(\d+)\.\d+$", anchor_id)
            if not id_match:
                continue
            kat_id = id_match.group(1)
            absolute_url = f"{BASE_URL}/index.php?kat={kat_id}"
            if absolute_url not in urls:
                urls.append(absolute_url)
        return urls

    def _parse_session_acts(self, session_html: str, *, now: datetime) -> list[LegalAct]:
        """Parse individual uchwały from a single session page."""
        soup = BeautifulSoup(session_html, "html.parser")
        results: list[LegalAct] = []
        for anchor in soup.select("#maincontent li.W2Kempty a[href]"):
            text = anchor.get_text(strip=True)
            if not text.upper().startswith("UCHWAŁA"):
                continue

            href = _normalized_href(anchor.get("href"))
            if not href:
                continue

            absolute_href = urljoin(BASE_URL, href)
            kat_id = _kat_from_url(absolute_href)
            if not kat_id:
                continue

            m = ACT_TITLE_RE.search(text)
            if m is None:
                published_at: datetime = now
            else:
                date_str = m.group(2)
                published_at = datetime.strptime(date_str, "%d.%m.%Y").replace(tzinfo=UTC)

            results.append(
                LegalAct(
                    stable_id=f"chorzow-uchwala-{kat_id}",
                    title=text,
                    published_at=published_at,
                    source_url=HTTP_URL_ADAPTER.validate_python(absolute_href),
                )
            )
        return results


# ------------------------------------------------------------------
# Module-level pure helpers
# ------------------------------------------------------------------


def _kat_from_url(url: str) -> str | None:
    """Extract the ``kat`` query-parameter value from *url*, or ``None``."""
    parsed = urlparse(url)
    values = parse_qs(parsed.query).get("kat", [])
    return values[0] if values else None
