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
from datetime import UTC, datetime

from bs4 import BeautifulSoup
from pydantic import HttpUrl, TypeAdapter

from bip_scraper.cities.base import BaseScraper
from bip_scraper.models import CitySlug, LegalAct

BASE_URL = "https://bip.gliwice.eu"
ACTS_PATH = "/radaMiasta/uchwaly"
DATE_RE = re.compile(r"Z dnia (\d{2}-\d{2}-\d{4})", re.IGNORECASE)
ACT_ID_RE = re.compile(r"/(\d+)$")

HTTP_URL_ADAPTER: TypeAdapter[HttpUrl] = TypeAdapter(HttpUrl)


class GliwiceScraper(BaseScraper):
    """Scraper for the Gliwice BIP council resolutions portal."""

    _follow_redirects = True

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
            act = _parse_row(row)
            if act:
                results.append(act)
        return results


def _parse_row(row) -> LegalAct | None:
    opis = row.find("div", class_="uchwaly-opis")
    p = opis.find("p") if opis else None
    if not p:
        return None
    strong = p.find("strong")
    if not strong or "uchwała" not in strong.get_text(strip=True).lower():
        return None
    title = strong.get_text(strip=True)
    # Extract date
    p_text = p.get_text(" ", strip=True)
    date_match = DATE_RE.search(p_text)
    if not date_match:
        return None
    published_at = datetime.strptime(date_match.group(1), "%d-%m-%Y").replace(tzinfo=UTC)
    # Extract source URL
    link = p.find("a", href=True)
    href = link["href"] if link else ""
    if not href.startswith("http"):
        href = BASE_URL + href
    id_match = ACT_ID_RE.search(href)
    if not link or not id_match:
        return None
    act_id = id_match.group(1)
    source_url = f"{BASE_URL}/rada-miasta/uchwaly/{act_id}"
    return LegalAct(
        stable_id=f"gliwice-uchwala-{act_id}",
        title=title,
        published_at=published_at,
        source_url=HTTP_URL_ADAPTER.validate_python(source_url),
    )
