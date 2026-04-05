"""Scraper stub for Zabrze BIP.

The Zabrze BIP (https://bip.miastozabrze.pl/rm/rm_uchwaly) requires
JavaScript to load content and cannot be scraped with static HTTP requests.

TODO: Implement using a headless browser (e.g., playwright) once the
infrastructure is available.
"""

from __future__ import annotations

from datetime import datetime

from bip_scraper.models import CitySlug, LegalAct


class ZabrzeScraper:
    @property
    def city(self) -> CitySlug:
        return CitySlug.ZABRZE

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        _ = now
        return []
