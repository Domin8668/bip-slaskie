"""Scraper stub for Sosnowiec BIP.

The Sosnowiec BIP (https://bip.um.sosnowiec.pl) uses the Madkom system.
Individual council resolutions for the current term (IX kadencja, 2024-2029)
are not published in the BIP registry — only session metadata is available.
Session articles link to the eSesja platform (sosnowiec.esesja.pl).

TODO: Implement once resolutions are published at:
  https://bip.um.sosnowiec.pl  (menuId=6126, Prawo Lokalne > Uchwały)
"""

from __future__ import annotations

from datetime import datetime

from bip_scraper.models import CitySlug, LegalAct


class SosnowiecScraper:
    @property
    def city(self) -> CitySlug:
        return CitySlug.SOSNOWIEC

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        _ = now
        return []
