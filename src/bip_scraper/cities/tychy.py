"""Scraper stub for Tychy BIP.

The Tychy BIP URL is https://bip.tychy.pl but DNS resolution fails
from the current environment.

TODO: Verify BIP URL and implement once the domain is accessible.
"""

from __future__ import annotations

from datetime import datetime

from bip_scraper.models import CitySlug, LegalAct


class TychyScraper:
    @property
    def city(self) -> CitySlug:
        return CitySlug.TYCHY

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        _ = now
        return []
