from datetime import UTC, datetime

from bip_scraper.cities.sosnowiec import SosnowiecScraper
from bip_scraper.models import CitySlug


def test_sosnowiec_scrape_acts_returns_empty() -> None:
    scraper = SosnowiecScraper()
    acts = scraper.scrape_acts(now=datetime(2026, 4, 5, tzinfo=UTC))
    assert acts == []


def test_sosnowiec_city_slug() -> None:
    scraper = SosnowiecScraper()
    assert scraper.city == CitySlug.SOSNOWIEC
