from __future__ import annotations

from datetime import datetime

from bip_scraper.models import CitySlug, LegalAct


class SwietochlowiceScraper:
    @property
    def city(self) -> CitySlug:
        return CitySlug.SWIETOCHLOWICE

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        _ = now
        return []
