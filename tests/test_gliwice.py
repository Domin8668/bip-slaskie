from datetime import UTC, datetime
from pathlib import Path

from bip_scraper.cities.gliwice import GliwiceScraper
from bip_scraper.models import CitySlug

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def test_gliwice_parse_acts_returns_acts() -> None:
    scraper = GliwiceScraper()
    acts = scraper._parse_acts(_read_fixture("gliwice_acts.html"))

    # 2 "uchwała" rows; "Stanowisko" row must be skipped
    assert len(acts) == 2
    for act in acts:
        assert act.stable_id.startswith("gliwice-uchwala-")


def test_gliwice_parse_acts_fields() -> None:
    scraper = GliwiceScraper()
    acts = scraper._parse_acts(_read_fixture("gliwice_acts.html"))

    act = acts[0]
    assert act.stable_id == "gliwice-uchwala-45678"
    assert act.published_at == datetime(2026, 3, 26, tzinfo=UTC)
    assert "Uchwała" in act.title
    assert "1234" in act.title
    assert str(act.source_url) == "https://bip.gliwice.eu/rada-miasta/uchwaly/45678"


def test_gliwice_parse_acts_skips_non_uchwaly() -> None:
    scraper = GliwiceScraper()
    acts = scraper._parse_acts(_read_fixture("gliwice_acts.html"))

    stable_ids = {a.stable_id for a in acts}
    # "Stanowisko" row (45700) must not appear
    assert "gliwice-uchwala-45700" not in stable_ids


def test_gliwice_stable_id_prefix() -> None:
    scraper = GliwiceScraper()
    acts = scraper._parse_acts(_read_fixture("gliwice_acts.html"))

    for act in acts:
        assert act.stable_id.startswith("gliwice-uchwala-")


def test_gliwice_has_next_page_true() -> None:
    scraper = GliwiceScraper()
    assert scraper._has_next_page(_read_fixture("gliwice_acts.html")) is True


def test_gliwice_has_next_page_false() -> None:
    scraper = GliwiceScraper()
    assert scraper._has_next_page(_read_fixture("gliwice_acts_last_page.html")) is False


def test_gliwice_parse_acts_no_table() -> None:
    scraper = GliwiceScraper()
    acts = scraper._parse_acts("<html><body><p>Brak tabeli</p></body></html>")
    assert acts == []


def test_gliwice_city_slug() -> None:
    scraper = GliwiceScraper()
    assert scraper.city == CitySlug.GLIWICE
