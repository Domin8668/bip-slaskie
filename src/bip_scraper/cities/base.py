from __future__ import annotations

from datetime import datetime
from typing import Protocol

from bip_scraper.models import CitySlug, LegalAct


class CityScraper(Protocol):
    @property
    def city(self) -> CitySlug:
        ...

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        ...
