"""Scraper stub for Bytom BIP.

The Bytom BIP URL is https://bip.um.bytom.pl but the server is not
accessible from the current environment (connection timeout).

TODO: Verify BIP URL and implement once the server is accessible.
"""

from __future__ import annotations

from datetime import datetime

from bip_scraper.models import CitySlug, LegalAct


class BytomScraper:
    @property
    def city(self) -> CitySlug:
        return CitySlug.BYTOM

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        _ = now
        return []
