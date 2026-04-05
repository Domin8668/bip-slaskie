"""Scraper stub for Rybnik BIP.

The Rybnik BIP URL is https://bip.rybnik.eu but DNS resolution fails
from the current environment.

TODO: Verify BIP URL and implement once the domain is accessible.
"""

from __future__ import annotations

from datetime import datetime

from bip_scraper.models import CitySlug, LegalAct


class RybnikScraper:
    @property
    def city(self) -> CitySlug:
        return CitySlug.RYBNIK

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        _ = now
        return []
