"""Scraper for Rybnik BIP uchwały Rady Miasta.

Navigation: single-page registry table at Default.aspx?Page=247 with all
historical resolutions. Acts are filtered to the current and previous year.

BIP URL: https://bip.um.rybnik.eu/
"""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup
from pydantic import HttpUrl, TypeAdapter

from bip_scraper.cities.base import BaseScraper
from bip_scraper.cities.base import normalized_href as _normalized_href
from bip_scraper.models import CitySlug, LegalAct

BASE_URL = "https://bip.um.rybnik.eu"
ACTS_URL = "https://bip.um.rybnik.eu/Default.aspx?Page=247"
HTTP_URL_ADAPTER: TypeAdapter[HttpUrl] = TypeAdapter(HttpUrl)


class RybnikScraper(BaseScraper):
    """Scraper for the Rybnik BIP council resolutions portal."""

    _follow_redirects = True

    def __init__(self, *, timeout_seconds: float = 30.0, max_retries: int = 3) -> None:
        super().__init__(timeout_seconds=timeout_seconds, max_retries=max_retries)

    @property
    def city(self) -> CitySlug:
        return CitySlug.RYBNIK

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        page_html = self._get_text(ACTS_URL)
        acts = self._parse_acts(page_html, now=now)
        if not acts:
            raise RuntimeError("Rybnik scraper: no legal acts parsed from the registry page")
        return sorted(acts, key=lambda a: a.stable_id)

    def _parse_acts(self, page_html: str, *, now: datetime) -> list[LegalAct]:
        soup = BeautifulSoup(page_html, "html.parser")
        min_year = now.year - 1
        results: list[LegalAct] = []

        # The first registry table contains the resolutions
        table = soup.select_one("table.registry")
        if table is None:
            return results

        for row in table.select("tbody tr"):
            act = _parse_row(row, min_year)
            if act:
                results.append(act)
        return results


def _parse_row(row, min_year: int) -> LegalAct | None:
    cells = row.select("td")
    if len(cells) < 4:
        return None

    number_text = cells[0].get_text(strip=True)
    date_text = cells[1].get_text(strip=True)
    title_text = cells[2].get_text(" ", strip=True)
    detail_link = cells[3].select_one("a[href]")

    if not date_text or not detail_link:
        return None

    published_at = _parse_date(date_text)
    if published_at is None or published_at.year < min_year:
        return None

    href = _normalized_href(detail_link.get("href"))
    absolute_url = urljoin(BASE_URL, href)
    act_id = _extract_id_param(href)
    if act_id is None:
        return None

    full_title = f"{number_text} — {title_text}" if number_text else title_text

    return LegalAct(
        stable_id=f"rybnik-uchwala-{act_id}",
        title=full_title,
        published_at=published_at,
        source_url=HTTP_URL_ADAPTER.validate_python(absolute_url),
    )


def _parse_date(text: str) -> datetime | None:
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        return None


def _extract_id_param(href: str) -> str | None:
    parsed = urlparse(href)
    values = parse_qs(parsed.query).get("Id", [])
    return values[0] if values else None
