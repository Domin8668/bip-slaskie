from datetime import UTC, datetime

from bip_scraper.cities.zabrze import ZabrzeScraper
from bip_scraper.models import CitySlug


def test_zabrze_scrape_acts_returns_empty() -> None:
    scraper = ZabrzeScraper()
    acts = scraper.scrape_acts(now=datetime(2026, 4, 5, tzinfo=UTC))
    assert acts == []


def test_zabrze_city_slug() -> None:
    scraper = ZabrzeScraper()
    assert scraper.city == CitySlug.ZABRZE
