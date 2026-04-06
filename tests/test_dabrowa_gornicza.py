from datetime import UTC, datetime
from pathlib import Path

from bip_scraper.cities.dabrowa_gornicza import DabrowaGorniczaScraper
from bip_scraper.models import CitySlug

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def test_dabrowa_gornicza_parse_acts_returns_acts() -> None:
    scraper = DabrowaGorniczaScraper()
    acts = scraper._parse_acts(_read_fixture("dabrowa_gornicza_acts.html"))

    # 2 valid divs; the malformed div (missing span) must be skipped
    assert len(acts) == 2
    for act in acts:
        assert act.stable_id.startswith("dabrowa-gornicza-uchwala-")
        assert act.published_at.tzinfo is not None


def test_dabrowa_gornicza_parse_acts_fields() -> None:
    scraper = DabrowaGorniczaScraper()
    acts = scraper._parse_acts(_read_fixture("dabrowa_gornicza_acts.html"))

    act = acts[0]
    assert act.stable_id == "dabrowa-gornicza-uchwala-56789"
    assert act.published_at == datetime(2026, 3, 26, tzinfo=UTC)
    assert "Nr XLVIII/987/2026" in act.title
    assert "Uchwała" in act.title
    assert str(act.source_url).startswith("https://www.bip.dabrowa-gornicza.pl/181640/dokument/")


def test_dabrowa_gornicza_stable_id_prefix() -> None:
    scraper = DabrowaGorniczaScraper()
    acts = scraper._parse_acts(_read_fixture("dabrowa_gornicza_acts.html"))

    for act in acts:
        assert act.stable_id.startswith("dabrowa-gornicza-uchwala-")


def test_dabrowa_gornicza_city_slug() -> None:
    scraper = DabrowaGorniczaScraper()
    assert scraper.city == CitySlug.DABROWAG
