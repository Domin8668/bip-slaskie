from __future__ import annotations

from datetime import datetime

from bip_scraper.cities.base import BaseScraper
from bip_scraper.cities.base import parse_acts_from_links as _parse_acts_from_links
from bip_scraper.models import CitySlug, LegalAct

BASE_URL = "https://www.siemianowice.pl"
UCHWALY_LIST_URL = f"{BASE_URL}/bip/rada-miasta/uchwaly/"


class SiemianowiceScraper(BaseScraper):
    """Scraper for Siemianowice Śląskie BIP council resolutions portal."""

    @property
    def city(self) -> CitySlug:
        return CitySlug.SIEMIANOWICE

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        """Fetch and return all uchwały from the city council."""
        try:
            list_html = self._get_text(UCHWALY_LIST_URL)
            acts = self._parse_acts_from_html(list_html, now=now)
            if not acts:
                raise RuntimeError("Siemianowice scraper: no legal acts parsed")
            return sorted(acts, key=lambda a: a.stable_id)
        except Exception as exc:
            raise RuntimeError("Siemianowice scraper: failed to scrape acts") from exc

    def _parse_acts_from_html(self, page_html: str, *, now: datetime) -> list[LegalAct]:
        """Parse uchwały from the main listing page."""
        return _parse_acts_from_links(
            page_html,
            base_url=BASE_URL,
            stable_id_prefix="siemianowice-uchwala",
            now=now,
        )
